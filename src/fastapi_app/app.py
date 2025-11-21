import hashlib
import json
import logging
import os
import pathlib
import shutil
import tempfile
import traceback
import uuid
from datetime import datetime
from typing import Optional

import aiofiles
from azure.ai.documentintelligence.models import DocumentContentFormat
from azure.monitor.opentelemetry import configure_azure_monitor
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.sql import func
from sqlmodel import Session, select

from . import config
from .models import Question, Restaurant, Review, User, engine

# Setup logger and Azure Monitor:
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    configure_azure_monitor()


# Setup FastAPI app:
app = FastAPI(docs_url=None, redoc_url=None)  # Disable Swagger UI and ReDoc
parent_path = pathlib.Path(__file__).parent.parent
app.mount("/mount", StaticFiles(directory=parent_path / "static"), name="static")
templates = Jinja2Templates(directory=parent_path / "templates")
templates.env.globals["prod"] = os.environ.get("RUNNING_IN_PRODUCTION", False)
# Use relative path for url_for, so that it works behind a proxy like Codespaces
templates.env.globals["url_for"] = app.url_path_for


# Dependency to get the database session
def get_db_session():
    with Session(engine) as session:
        yield session


# ===== Pydantic Models for User Management =====

class UserCreate(BaseModel):
    username: str
    display_name: Optional[str] = None
    password: str
    is_admin: bool = False
    is_active: bool = True


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    display_name: Optional[str] = None
    is_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    id: uuid.UUID
    username: str
    display_name: Optional[str] = None
    is_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ===== Utility Functions =====

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    if password is None or password == "":
        raise HTTPException(status_code=400, detail="Password is required.")
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify configuration and service status.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "is_azure": os.getenv("WEBSITE_HOSTNAME") is not None,
            "website_hostname": os.getenv("WEBSITE_HOSTNAME", "localhost")
        },
        "services": {
            "database": "unknown",
            "azure_document_intelligence": "not_configured",
            "openai": "not_configured"
        },
        "configuration": {
            "openai_model": config.openai_model,
            "default_uploaded_by": config.default_uploaded_by
        }
    }
    
    # Check Azure Document Intelligence
    if config.client:
        health_status["services"]["azure_document_intelligence"] = "configured"
    else:
        health_status["services"]["azure_document_intelligence"] = "not_configured"
        health_status["status"] = "degraded"
    
    # Check OpenAI
    if config.openai_client:
        health_status["services"]["openai"] = "configured"
    else:
        health_status["services"]["openai"] = "not_configured"
        health_status["status"] = "degraded"
    
    # Check database connection
    try:
        with Session(engine) as session:
            session.exec(select(User).limit(1))
        health_status["services"]["database"] = "connected"
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return JSONResponse(content=health_status)


async def cleanup_temp_dir(temp_dir: str):
    """Clean up temporary directory."""
    try:
        if os.path.exists(temp_dir):
            await run_in_threadpool(shutil.rmtree, temp_dir, ignore_errors=True)
            logger.info(f"🧹 Cleaned temp dir: {temp_dir}")
    except Exception as e:
        logger.error(f"Temp cleanup failed: {e}")


# ===== Azure Document Intelligence Extraction =====

async def extract_markdown_from_pdf_azure(pdf_path: str) -> dict:
    """Extract markdown content from PDF using Azure Document Intelligence."""
    if not config.client:
        raise HTTPException(
            status_code=503,
            detail="Azure Document Intelligence client not configured. Please set AZURE_DOC_INTELLIGENCE_ENDPOINT and AZURE_DOC_INTELLIGENCE_KEY."
        )
    
    try:
        async with aiofiles.open(pdf_path, "rb") as f:
            pdf_content = await f.read()
        
        poller = await config.client.begin_analyze_document(
            "prebuilt-layout",
            body=pdf_content,
            output_content_format=DocumentContentFormat.MARKDOWN,
        )
        result = await poller.result()
        
        full_content = getattr(result, "content", "") or ""
        pages = getattr(result, "pages", []) or []
        languages = getattr(result, "languages", []) or []
        
        # Build paragraphs by page
        paragraphs_by_page = {}
        for paragraph in getattr(result, "paragraphs", []) or []:
            bounding_regions = getattr(paragraph, "bounding_regions", []) or []
            for region in bounding_regions:
                page_number = getattr(region, "page_number", None)
                if page_number is None:
                    continue
                paragraphs_by_page.setdefault(page_number, []).append(paragraph)
        
        # Extract page data
        pages_data = []
        for idx, page in enumerate(pages):
            page_number = getattr(page, "page_number", idx + 1)
            page_content = getattr(page, "content", None)
            
            if not page_content:
                spans = getattr(page, "spans", []) or []
                if spans and full_content:
                    fragments = []
                    for span in spans:
                        start = getattr(span, "offset", None)
                        length = getattr(span, "length", None)
                        if start is None or length is None:
                            continue
                        fragments.append(full_content[start : start + length])
                    page_content = "".join(fragments)
            
            if not page_content:
                paragraphs = paragraphs_by_page.get(page_number, [])
                page_content = "\n".join(
                    getattr(para, "content", "") for para in paragraphs if getattr(para, "content", "")
                )
            
            pages_data.append(
                {
                    "page_number": page_number,
                    "content": (page_content or "").strip(),
                }
            )
        
        return {
            "page_count": len(pages),
            "languages": [lang.locale for lang in languages if getattr(lang, "locale", None)],
            "full_content": full_content,
            "pages": pages_data,
        }
    
    except Exception as e:
        logger.error(f"Azure extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Azure extraction failed: {e}")


# ===== OpenAI Question Extraction =====

async def extract_questions_from_markdown(markdown_content: str, page_metadata: dict) -> list:
    """Extract questions from markdown content using OpenAI."""
    if not config.openai_client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI client not configured. Please set OPENAI_API_KEY."
        )
    
    # Arabic extraction prompt
    arabic_prompt = f"""أنت خبير في التعليم متخصص في استخراج الأسئلة والمسائل من الكتب التعليمية الرقمية والمطبوعة. لديك خبرة عميقة في:

        - الرياضيات: الأعداد المركبة، الجذور، الجبر، المعادلات، التفاضل والتكامل، الإحصاء
        - الفيزياء: الصيغ الفيزيائية، الوحدات، الثوابت (مثل c, h, G, k)، الميكانيكا، الكهرباء، المغناطيسية
        - الأحياء: المصطلحات البيولوجية، الأسماء العلمية للكائنات، التركيب الخلوي، العمليات الحيوية
        - الكيمياء: الصيغ الكيميائية، المعادلات الكيميائية، الجدول الدوري، التفاعلات
        - الرموز والترميز: الرموز الرياضية (∑, ∫, ∂, ∇, ∞, π, e، √، ≠، ≤، ≥، ±، ≈)
        - الرموز الفيزيائية (Δ, λ, μ, σ, θ، Ω، α، β)
        - الرموز الكيميائية (H₂O، CO₂، NaCl، Fe³⁺، OH⁻ وغيرها)
        - المصطلحات العلمية: المصطلحات المتخصصة بالعربية والإنجليزية
        - بنية المحتوى التعليمي: الوحدات الدراسية، العناوين، الأمثلة، التمارين، الأسئلة، الأنشطة

        مهمتك الأساسية: استخراج جميع الأسئلة والتدريبات من النص المقدم بدقة عالية، مع الحفاظ على **كل الرموز والصيغ العلمية والرياضية والكيميائية كما وردت في الأصل تماماً** من حيث الشكل، والأحرف، والمسافات، دون أي تعديل أو تحويل إلى نصوص بديلة.

        التعليمات الإضافية الدقيقة:
        1. لا تكتب أو تشرح أي شيء خارج مصفوفة JSON النهائية.
        2. استخرج جميع أنواع الأسئلة بما في ذلك الأسئلة المحلولة أو الجزئية أو المتعددة الأجزاء.
        3. احفظ كل الرموز كما هي — مثل الجذر التربيعي (√)، التكامل (∫)، المجموع (∑)، الأس (x²)، المعاملات الكيميائية (H₂، CO₂...)، وأي أشكال هندسية أو أسهم أو كسور.
        4. لا تفسر الرموز أو تحاول كتابتها بالحروف (مثل كتابة √ بدلاً من "جذر").
        5. احتفظ باللغة الأصلية كما في المصدر، سواء عربية أو إنجليزية أو غيرها.
        6. اتبع القيم التالية فقط:
           - "question_type": "Descriptive" | "Multiple Choice" | "True/False" | "Short Answer"
           - "question_difficulty": "Easy" | "Medium" | "Hard"
        7. اترك الحقول الفارغة كما هي (مثل "page_number").
        8. لا تضف علامات تنسيق (Markdown، LaTeX، HTML) إلى النصوص أو الرموز.
        9. لا تُدرج تعليقات أو نصوص خارج JSON؛ أعد فقط مصفوفة JSON بالصيغ التالية:

        [
        {{
            "lesson_title": "اسم الدرس أو الوحدة" (إجباري),
            "question": "نص السؤال الكامل كما ورد في المصدر، مع الحفاظ على الرموز الدقيقة (مثل √x، H₂O، ∫ x dx، Na⁺، ΔE = mc²، إلخ)",
            "question_type": "Descriptive|Multiple Choice|True/False|Fill in the blank|Short Answer" (إجباري),
            "question_difficulty": "Easy|Medium|Hard" (إجباري),
            "page_number": "",
            "answer_steps": "خطوات الحل أو التفسير إن وجدت (اختياري)",
            "correct_answer": "الإجابة النهائية إن وجدت (اختياري)"
        }}
        ]

المحتوى للتحليل (Markdown):
{markdown_content}

أعد مصفوفة JSON فقط دون أي شروحات إضافية."""

    try:
        response = await config.openai_client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {"role": "system", "content": "أنت خبير في التعليم متخصص في تحليل المحتوى واستخراج الأسئلة من الكتب."},
                {"role": "user", "content": arabic_prompt}
            ],
            temperature=0.05,
            max_tokens=8000,
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Remove markdown code block markers if present
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()
        
        questions = json.loads(result_text)
        
        if not isinstance(questions, list):
            raise ValueError("Expected a list of questions in JSON array.")
        
        for q in questions:
            if not isinstance(q, dict):
                raise ValueError("Each question entry must be a JSON object.")
        
        return questions
    
    except Exception as e:
        logger.error(f"OpenAI extraction error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"OpenAI extraction failed: {e}")


# ===== Database Persistence =====

async def store_questions_in_db(
    session: Session,
    questions: list,
    file_name: str,
    subject_name: str,
    class_name: Optional[str] = None,
    specialization: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    updated_by: Optional[str] = None,
):
    """Store extracted questions in the database."""
    if not questions:
        return
    
    if not file_name:
        logger.error("File name is required to store questions.")
        raise HTTPException(status_code=500, detail="File name is missing for database insert.")
    
    subject_name_value = str(subject_name).strip() if subject_name and str(subject_name).strip() else None
    if not subject_name_value:
        logger.error("Provided subject_name is missing or empty.")
        raise HTTPException(status_code=400, detail="subject_name is required.")
    
    class_name_value = str(class_name).strip() if class_name and str(class_name).strip() else None
    specialization_value = str(specialization).strip() if specialization and str(specialization).strip() else None
    
    uploaded_by_value = None
    if uploaded_by and str(uploaded_by).strip():
        uploaded_by_value = str(uploaded_by).strip()
    elif config.default_uploaded_by and str(config.default_uploaded_by).strip():
        uploaded_by_value = str(config.default_uploaded_by).strip()
    
    if not uploaded_by_value:
        logger.error("Uploader information is missing.")
        raise HTTPException(status_code=400, detail="uploaded_by is required.")
    
    updated_by_value = None
    if updated_by is not None and str(updated_by).strip():
        updated_by_value = str(updated_by).strip()
    elif config.default_updated_by and str(config.default_updated_by).strip():
        updated_by_value = str(config.default_updated_by).strip()
    
    allowed_question_types = {
        "Descriptive",
        "Multiple Choice",
        "True/False",
        "Fill in the blank",
        "Short Answer",
    }
    allowed_difficulties = {"Easy", "Medium", "Hard"}
    
    for q in questions:
        try:
            question_text_raw = q.get("question")
            question_type_raw = q.get("question_type")
            question_difficulty_raw = q.get("question_difficulty")
            page_number_raw = q.get("page_number")
            answer_steps_raw = q.get("answer_steps")
            correct_answer_raw = q.get("correct_answer")
            lesson_title_raw = q.get("lesson_title")
        except (KeyError, ValueError, TypeError) as exc:
            logger.error(f"Invalid question payload for DB insert: {exc} - data: {q}")
            raise HTTPException(status_code=500, detail="Invalid question data received from extraction.") from exc
        
        if question_text_raw is None or str(question_text_raw).strip() == "":
            logger.error(f"Missing question text for generated question payload: {q}")
            raise HTTPException(status_code=500, detail="Missing question text for database insert.")
        
        question_text = str(question_text_raw).strip()
        
        question_type = str(question_type_raw).strip() if question_type_raw else None
        if question_type and question_type not in allowed_question_types:
            logger.warning(f"Unsupported question_type '{question_type}' received. Storing as NULL.")
            question_type = None
        
        question_difficulty = str(question_difficulty_raw).strip() if question_difficulty_raw else None
        if question_difficulty and question_difficulty not in allowed_difficulties:
            logger.warning(f"Unsupported question_difficulty '{question_difficulty}' received. Storing as NULL.")
            question_difficulty = None
        
        page_number = None
        if page_number_raw is not None and str(page_number_raw).strip() != "":
            page_number = str(page_number_raw).strip()
        
        answer_steps = str(answer_steps_raw).strip() if answer_steps_raw and str(answer_steps_raw).strip() else None
        correct_answer = str(correct_answer_raw).strip() if correct_answer_raw and str(correct_answer_raw).strip() else None
        lesson_title = str(lesson_title_raw).strip() if lesson_title_raw and str(lesson_title_raw).strip() else None
        
        if not lesson_title:
            logger.error(f"Missing lesson_title for generated question payload: {q}")
            raise HTTPException(status_code=500, detail="Missing lesson name for database insert.")
        
        # Create Question object using SQLModel
        new_question = Question(
            id=uuid.uuid4(),
            file_name=file_name,
            subject_name=subject_name_value,
            lesson_title=lesson_title,
            class_name=class_name_value,
            specialization=specialization_value,
            question=question_text,
            question_type=question_type,
            question_difficulty=question_difficulty,
            page_number=page_number,
            answer_steps=answer_steps,
            correct_answer=correct_answer,
            uploaded_by=uploaded_by_value,
            updated_by=updated_by_value,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        session.add(new_question)
    
    try:
        session.commit()
        logger.info(f"🗃️ Stored {len(questions)} questions in database.")
    except Exception as exc:
        session.rollback()
        logger.error(f"Failed to persist questions: {exc}")
        raise HTTPException(status_code=500, detail="Failed to persist questions to database.") from exc


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page showing API documentation and solution description."""
    logger.info("root called")
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "is_azure": config.client is not None,
        "is_openai": config.openai_client is not None
    })



# ===== User Management Endpoints =====

@app.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(user_data: UserCreate, session: Session = Depends(get_db_session)):
    """Create a new user."""
    logger.info("Creating new user: %s", user_data.username)
    
    # Check if username already exists
    existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash the password
    password_hash = hash_password(user_data.password)
    
    # Create new user
    new_user = User(
        id=uuid.uuid4(),
        username=user_data.username,
        display_name=user_data.display_name,
        password_hash=password_hash,
        is_admin=user_data.is_admin,
        is_active=user_data.is_active,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return new_user


@app.get("/users", response_model=list[UserResponse])
async def list_users(
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db_session)
):
    """List all users with pagination."""
    logger.info("Listing users with limit=%d, offset=%d", limit, offset)
    
    statement = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    users = session.exec(statement).all()
    
    return users


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    session: Session = Depends(get_db_session)
):
    """Update an existing user."""
    logger.info("Updating user: %s", user_id)
    
    # Find the user
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields if provided
    if user_data.display_name is not None:
        user.display_name = user_data.display_name
    
    if user_data.password is not None:
        user.password_hash = hash_password(user_data.password)
    
    if user_data.is_admin is not None:
        user.is_admin = user_data.is_admin
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    user.updated_at = datetime.now()
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


@app.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, session: Session = Depends(get_db_session)):
    """Authenticate a user and return user information."""
    logger.info("Login attempt for username: %s", login_data.username)
    
    # Find user by username
    user = session.exec(select(User).where(User.username == login_data.username)).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    
    # Verify password
    password_hash = hash_password(login_data.password)
    if password_hash != user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Return user information (excluding password_hash)
    return LoginResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        is_admin=user.is_admin,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


# ===== Question Extraction Endpoints =====

@app.post("/extract")
async def extract_questions(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    subject_name: Optional[str] = Form(None),
    class_name: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None),
    updated_by: Optional[str] = Form(None),
    session: Session = Depends(get_db_session),
):
    """
    Extract questions from PDF file using Azure Document Intelligence and OpenAI.
    
    - **file**: PDF file to extract questions from (required)
    - **subject_name**: Subject name (required, can be in metadata or form field)
    - **class_name**: Class name (optional)
    - **specialization**: Specialization (optional)
    - **uploaded_by**: Username who uploaded the file (required)
    - **updated_by**: Username who updated the file (optional)
    - **metadata**: JSON string containing any of the above fields (optional)
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    temp_dir = await run_in_threadpool(tempfile.mkdtemp)
    pdf_path = os.path.join(temp_dir, file.filename)
    
    try:
        # Parse metadata if provided
        metadata_values = {}
        if metadata:
            try:
                metadata_values = json.loads(metadata)
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {exc}") from exc
        
        # Extract and validate subject_name
        subject_name_value_raw = subject_name if subject_name is not None else metadata_values.get("subject_name")
        subject_name_value = (
            subject_name_value_raw.strip()
            if isinstance(subject_name_value_raw, str) and subject_name_value_raw.strip()
            else None
        )
        if not subject_name_value:
            raise HTTPException(status_code=400, detail="subject_name is required.")
        
        # Extract optional fields
        class_name_value_raw = class_name if class_name is not None else metadata_values.get("class_name")
        class_name_value = (
            class_name_value_raw.strip()
            if isinstance(class_name_value_raw, str) and class_name_value_raw.strip()
            else None
        )
        
        specialization_value_raw = (
            specialization if specialization is not None else metadata_values.get("specialization")
        )
        specialization_value = (
            specialization_value_raw.strip()
            if isinstance(specialization_value_raw, str) and specialization_value_raw.strip()
            else None
        )
        
        uploaded_by_value_raw = uploaded_by if uploaded_by is not None else metadata_values.get("uploaded_by")
        uploaded_by_value = (
            uploaded_by_value_raw.strip()
            if isinstance(uploaded_by_value_raw, str) and uploaded_by_value_raw.strip()
            else None
        )
        if not uploaded_by_value:
            raise HTTPException(status_code=400, detail="uploaded_by is required.")
        
        updated_by_value_raw = updated_by if updated_by is not None else metadata_values.get("updated_by")
        updated_by_value = (
            updated_by_value_raw.strip()
            if isinstance(updated_by_value_raw, str) and updated_by_value_raw.strip()
            else None
        )
        
        # Save uploaded file
        async with aiofiles.open(pdf_path, "wb") as f:
            while chunk := await file.read(1_048_576):
                await f.write(chunk)
        
        # Extract content using Azure Document Intelligence
        extraction_result = await extract_markdown_from_pdf_azure(pdf_path)
        
        pages = extraction_result.get("pages") or []
        if not pages:
            raise HTTPException(status_code=500, detail="Azure Document Intelligence did not return any pages.")
        
        total_pages = extraction_result.get("page_count") or len(pages)
        languages = extraction_result.get("languages") or ["ar"]
        
        pages_attempted = 0
        pages_skipped = 0
        total_questions = 0
        page_summaries = []
        
        # Process each page
        for page_data in pages:
            page_number = page_data.get("page_number")
            page_content = (page_data.get("content") or "").strip()
            
            if not page_content:
                pages_skipped += 1
                page_summaries.append(
                    {
                        "page_number": page_number,
                        "questions_extracted": 0,
                        "status": "skipped_empty_content",
                    }
                )
                continue
            
            pages_attempted += 1
            page_metadata = {
                "page_number": page_number,
                "page_count": total_pages,
                "languages": languages,
            }
            
            try:
                extracted_questions = await extract_questions_from_markdown(page_content, page_metadata)
            except HTTPException as http_exc:
                page_summaries.append(
                    {
                        "page_number": page_number,
                        "questions_extracted": 0,
                        "status": "failed",
                        "error": http_exc.detail,
                    }
                )
                raise
            except Exception as exc:
                page_summaries.append(
                    {
                        "page_number": page_number,
                        "questions_extracted": 0,
                        "status": "failed",
                        "error": str(exc),
                    }
                )
                raise HTTPException(status_code=500, detail=f"OpenAI extraction failed for page {page_number}: {exc}") from exc
            
            # Sanitize and enrich questions
            sanitized_questions = []
            for question in extracted_questions:
                if not isinstance(question, dict):
                    logger.error(f"Question payload is not a dictionary: {question}")
                    raise HTTPException(status_code=500, detail="Invalid question format received from extraction.")
                
                normalized_question = dict(question)
                normalized_question["page_number"] = str(page_number) if page_number is not None else None
                normalized_question["subject_name"] = subject_name_value
                normalized_question["class_name"] = class_name_value
                normalized_question["specialization"] = specialization_value
                normalized_question["uploaded_by"] = uploaded_by_value
                normalized_question["updated_by"] = updated_by_value
                
                lesson_title_raw = normalized_question.get("lesson_title")
                if lesson_title_raw is None or str(lesson_title_raw).strip() == "":
                    normalized_question["lesson_title"] = subject_name_value
                else:
                    normalized_question["lesson_title"] = str(lesson_title_raw).strip()
                
                if normalized_question.get("answer_steps") is not None:
                    answer_steps_value = str(normalized_question["answer_steps"]).strip()
                    normalized_question["answer_steps"] = answer_steps_value or None
                
                if normalized_question.get("correct_answer") is not None:
                    correct_answer_value = str(normalized_question["correct_answer"]).strip()
                    normalized_question["correct_answer"] = correct_answer_value or None
                
                sanitized_questions.append(normalized_question)
            
            # Store questions in database
            await store_questions_in_db(
                session,
                sanitized_questions,
                file.filename,
                subject_name_value,
                class_name_value,
                specialization_value,
                uploaded_by_value,
                updated_by_value,
            )
            
            questions_count = len(sanitized_questions)
            total_questions += questions_count
            
            page_summaries.append(
                {
                    "page_number": page_number,
                    "questions_extracted": questions_count,
                    "status": "processed" if questions_count else "processed_no_questions",
                }
            )
        
        status_message = (
            f"Processed {pages_attempted} page(s); stored {total_questions} question(s)."
            if total_questions
            else "Processed pages but no questions were extracted."
        )
        
        response_payload = {
            "status": "success",
            "message": status_message,
            "summary": {
                "total_pages_detected": total_pages,
                "pages_with_content": pages_attempted,
                "pages_skipped": pages_skipped,
                "questions_stored": total_questions,
                "pages": page_summaries,
            },
        }
        
        background_tasks.add_task(cleanup_temp_dir, temp_dir)
        
        return JSONResponse(status_code=200, content=response_payload)
    
    except HTTPException as http_exc:
        background_tasks.add_task(cleanup_temp_dir, temp_dir)
        logger.error(f"Error: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        background_tasks.add_task(cleanup_temp_dir, temp_dir)
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}") from e


# ===== Question Management Endpoints =====

class QuestionResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    subject_name: str
    lesson_title: str
    class_name: Optional[str] = None
    specialization: Optional[str] = None
    question: str
    question_type: Optional[str] = None
    question_difficulty: Optional[str] = None
    page_number: Optional[str] = None
    answer_steps: Optional[str] = None
    correct_answer: Optional[str] = None
    uploaded_by: str
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@app.get("/questions", response_model=list[QuestionResponse])
async def list_questions(
    subject_name: Optional[str] = None,
    class_name: Optional[str] = None,
    specialization: Optional[str] = None,
    lesson_title: Optional[str] = None,
    question_type: Optional[str] = None,
    question_difficulty: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db_session)
):
    """
    List questions with optional filters and pagination.
    
    - **subject_name**: Filter by subject name
    - **class_name**: Filter by class name
    - **specialization**: Filter by specialization
    - **lesson_title**: Filter by lesson title
    - **question_type**: Filter by question type
    - **question_difficulty**: Filter by question difficulty
    - **limit**: Number of results to return (default: 100, max: 500)
    - **offset**: Number of results to skip (default: 0)
    """
    logger.info(f"Listing questions with filters: subject_name={subject_name}, class_name={class_name}")
    
    # Limit validation
    if limit > 500:
        limit = 500
    
    # Build query
    statement = select(Question)
    
    # Apply filters
    if subject_name:
        statement = statement.where(Question.subject_name == subject_name)
    if class_name:
        statement = statement.where(Question.class_name == class_name)
    if specialization:
        statement = statement.where(Question.specialization == specialization)
    if lesson_title:
        statement = statement.where(Question.lesson_title.contains(lesson_title))
    if question_type:
        statement = statement.where(Question.question_type == question_type)
    if question_difficulty:
        statement = statement.where(Question.question_difficulty == question_difficulty)
    
    # Order and paginate
    statement = statement.order_by(Question.created_at.desc()).limit(limit).offset(offset)
    
    questions = session.exec(statement).all()
    
    return questions


@app.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: uuid.UUID,
    session: Session = Depends(get_db_session)
):
    """Get a specific question by ID."""
    question = session.exec(select(Question).where(Question.id == question_id)).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return question
