from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import os
import sys
import fitz  # pymupdf
from google import genai
from dotenv import load_dotenv
from django.core.files.storage import FileSystemStorage
from .models import Customuser, SavedQuestion, ExamHistory
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.http import HttpResponse, JsonResponse
import json
import re

# Add GTK path to system path if on Windows
if os.name == 'nt':  # Windows
    # Add GTK installation paths to system path
    os_paths = [
        r'C:\Program Files\GTK3-Runtime Win64\bin',
        r'C:\Program Files (x86)\GTK3-Runtime Win64\bin', 
        r'C:\msys64\mingw64\bin',
        r'C:\GTK\bin'
    ]
    for path in os_paths:
        if os.path.exists(path) and path not in os.environ['PATH']:
            os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
            sys.path.append(path)

# Load environment
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Please set the 'GEMINI_API_KEY' environment variable.")

# Initialize Gemini Client
client = genai.Client(api_key=api_key)

# Function to extract text from uploaded PDF
def extract_text_from_pdf(uploaded_file):
    fs = FileSystemStorage()
    filename = fs.save(uploaded_file.name, uploaded_file)
    file_path = fs.path(filename)

    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()

    fs.delete(filename)  # Clean up
    return text

# Home view to handle upload and prediction - Removed login_required decorator
def home(request):
    # Check if user is authenticated for form submission
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to generate exam questions")
            return redirect('login')
            
        subject = request.POST.get('subject')
        syllabus_pdf = request.FILES.get('syllabus_pdf')
        pyq_pdf = request.FILES.get('pyq_pdf')
        
        # Get customization options
        question_count = int(request.POST.get('question_count', 5))
        difficulty = request.POST.get('difficulty', 'medium')
        specific_topics = request.POST.get('specific_topics', '')

        syllabus_text = extract_text_from_pdf(syllabus_pdf) if syllabus_pdf else ""
        pyq_text = extract_text_from_pdf(pyq_pdf) if pyq_pdf else ""

        # Adjust the prompt based on user preferences
        difficulty_instructions = {
            'easy': "Focus on fundamental concepts and straightforward applications. Avoid complex scenarios.",
            'medium': "Balance between fundamental concepts and some applications requiring deeper understanding.",
            'hard': "Focus on challenging applications, interconnected concepts, and scenarios requiring critical thinking."
        }

        topic_filter = ""
        if specific_topics:
            topic_filter = f"""
- Focus specifically on these topics: {specific_topics}
            """

        prompt = f"""
You are an AI university exam assistant specialized in creating high-quality practice exams.

Subject: {subject}

Task: Generate {question_count} likely exam questions with comprehensive answers.

#### Parameters:
- Difficulty: {difficulty.upper()} - {difficulty_instructions.get(difficulty, "")}
- Question format: Include a mix of question types appropriate for university-level assessment
{topic_filter}

#### Analysis Instructions:
1. Carefully analyze the provided syllabus content
2. Identify patterns and frequently tested concepts from previous year papers
3. Focus on topics that appear both in the syllabus and previous exams
4. If no previous papers are provided, focus on core concepts from the syllabus

#### For each question:
1. Write a clear, exam-like question
2. Provide a comprehensive answer (250-300 words)
3. Include 3-5 key points that should be included in any good answer
4. Note any common mistakes students make with this type of question

#### Output Format:
Format each question and answer pair exactly as follows:
Question 1: [Question text]
Answer 1: [Comprehensive answer]
Key Points: [Bulleted list]
Common Mistakes: [Brief notes]

[Repeat for each question]

#### Input Content:
Syllabus:
{syllabus_text or "No syllabus provided. Generate general academic questions for this subject based on standard curricula."}

Previous Year Questions:
{pyq_text or "No previous exam questions provided. Focus on fundamental concepts covered in most university courses on this subject."}
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt]
            )
            ai_response = response.candidates[0].content.parts[0].text
            
            # Store in session for later retrieval
            request.session['subject'] = subject
            request.session['ai_response'] = ai_response
            
            # Save to exam history with new fields
            exam_history = ExamHistory.objects.create(
                user=request.user,
                subject=subject,
                ai_response=ai_response,
                question_count=question_count,
                difficulty=difficulty,
                specific_topics=specific_topics if specific_topics else None
            )
            
            # Process the AI response to extract individual questions and answers
            questions_answers = parse_ai_response(ai_response)
            
            return render(request, 'result.html', {
                'subject': subject,
                'ai_response': ai_response,
                'questions_answers': questions_answers,
                'exam_history_id': exam_history.id
            })
        except Exception as e:
            messages.error(request, f"Error generating content: {str(e)}")
            return render(request, 'home.html', {'error': str(e)})

    return render(request, 'home.html')

def parse_ai_response(text):
    """Parse the AI response to extract individual questions and answers"""
    # This is a simplified parser - you might need to adjust based on actual response format
    questions_answers = []
    
    # Try to find question-answer pairs using regex
    pattern = r'(?:Question\s*(\d+):?\s*)(.*?)(?:Answer\s*\1:?\s*)(.*?)(?=Question\s*\d+:|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        for match in matches:
            question_num, question_text, answer_text = match
            questions_answers.append({
                'question_num': question_num.strip(),
                'question_text': question_text.strip(),
                'answer_text': answer_text.strip()
            })
    else:
        # Fallback if the regex doesn't match
        # Just return the whole text as one item
        questions_answers.append({
            'question_num': '1',
            'question_text': 'See full response below',
            'answer_text': text
        })
    
    return questions_answers

def register(request):
    if request.method == 'POST':
        firstnm = request.POST.get('first_name')
        lastnm = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')

        email = request.POST.get('email')
        dob = request.POST.get('dob')
        college = request.POST.get('college')
        address = request.POST.get('address')
        mob = request.POST.get('mob')

        # check user is already exists
        if Customuser.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists.'})
        if Customuser.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Email already exists.'})
        if Customuser.objects.filter(mob=mob).exists():
            return render(request, 'register.html', {'error': 'Mobile number already exists.'})

        else:
            # Create a new user
            user = Customuser.objects.create_user(
                first_name=firstnm,
                last_name=lastnm,
                username=username,
                email=email,
                dob=dob,
                college=college,
                address=address,
                mob=mob
            )
            user.set_password(password)  # Hash the password
            # Save the user to the database
            user.save()
            
            # Send welcome email
            try:
                from django.core.mail import send_mail
                from django.template.loader import render_to_string
                from django.utils.html import strip_tags
                
                subject = f"Welcome to SmartExam, {firstnm}!"
                html_message = render_to_string('emails/welcome_email.html', {
                    'user': user,
                    'site_name': 'SmartExam',
                })
                plain_message = strip_tags(html_message)
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = email
                
                send_mail(
                    subject, 
                    plain_message, 
                    from_email, 
                    [to_email], 
                    html_message=html_message,
                    fail_silently=True
                )
            except Exception as e:
                # Log the error but continue with registration
                print(f"Error sending welcome email: {str(e)}")
            
            return render(request, 'login.html', {'message': 'User registered successfully! Please check your email for login details.'})

    return render(request, 'register.html')


def login1(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('home')  # Replace '/' with your actual home URL
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('login1')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('/login/')  # Redirect to login page after logout


@login_required(login_url='/login/')
def result(request):
    # This view is for handling direct access to the result page
    # When accessed directly, redirect to home
    if not request.session.get('ai_response'):
        return redirect('home')
    
    # Get saved session data
    context = {
        'subject': request.session.get('subject', ''),
        'ai_response': request.session.get('ai_response', '')
    }
    
    return render(request, 'result.html', context)

@login_required(login_url='/login/')
def dashboard(request):
    """Display user's exam history and analytics"""
    # Get current user's exam history
    exam_history = ExamHistory.objects.filter(user=request.user)
    saved_questions = SavedQuestion.objects.filter(user=request.user)
    
    # Calculate some analytics
    total_questions = sum(history.question_count for history in exam_history)
    subject_stats = {}
    difficulty_stats = {'easy': 0, 'medium': 0, 'hard': 0}
    
    for history in exam_history:
        if history.subject in subject_stats:
            subject_stats[history.subject] += 1
        else:
            subject_stats[history.subject] = 1
        
        difficulty_stats[history.difficulty] += 1
    
    most_studied_subject = max(subject_stats.items(), key=lambda x: x[1])[0] if subject_stats else None
    
    context = {
        'exam_history': exam_history,
        'saved_questions': saved_questions,
        'total_questions': total_questions,
        'subject_stats': subject_stats,
        'difficulty_stats': difficulty_stats,
        'most_studied_subject': most_studied_subject,
        'exam_count': exam_history.count(),
        'saved_count': saved_questions.count()
    }
    
    return render(request, 'dashboard/history.html', context)

@login_required(login_url='/login/')
def save_question(request):
    """Save a question from an exam history to the user's saved questions"""
    if request.method == 'POST':
        exam_history_id = request.POST.get('exam_history_id')
        question_text = request.POST.get('question_text')
        answer_text = request.POST.get('answer_text')
        
        try:
            exam_history = ExamHistory.objects.get(id=exam_history_id, user=request.user)
            
            saved_question = SavedQuestion.objects.create(
                user=request.user,
                exam_history=exam_history,
                question_text=question_text,
                answer_text=answer_text
            )
            
            return JsonResponse({
                'success': True, 
                'message': 'Question saved successfully!'
            })
            
        except ExamHistory.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid request. Exam history not found.'
            }, status=404)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)

@login_required(login_url='/login/')
def add_note(request, question_id):
    """Add a note to a saved question"""
    if request.method == 'POST':
        note = request.POST.get('note')
        
        try:
            question = SavedQuestion.objects.get(id=question_id, user=request.user)
            question.notes = note
            question.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Note added successfully!'
            })
            
        except SavedQuestion.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Question not found'
            }, status=404)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request'
    }, status=400)

@login_required(login_url='/login/')
def delete_saved_question(request, question_id):
    """Delete a saved question"""
    try:
        question = SavedQuestion.objects.get(id=question_id, user=request.user)
        question.delete()
        
        return JsonResponse({
            'success': True, 
            'message': 'Question deleted successfully'
        })
        
    except SavedQuestion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Question not found'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required(login_url='/login/')
def export_questions(request, history_id):
    """Export questions as PDF or TXT based on user preference"""
    from io import BytesIO
    from django.template.loader import render_to_string
    
    # Get export format from request (default to 'pdf')
    export_format = request.GET.get('format', 'pdf')
    
    try:
        history = ExamHistory.objects.get(id=history_id, user=request.user)
        
        # Process AI response to extract individual questions and answers
        questions_answers = parse_ai_response(history.ai_response)
        
        # Handle text format export
        if export_format == 'txt':
            # Create plain text content
            text_content = f"Subject: {history.subject}\n"
            text_content += f"Difficulty: {history.difficulty}\n"
            text_content += f"Date: {history.created_at}\n\n"
            
            for qa in questions_answers:
                text_content += f"Question {qa['question_num']}:\n{qa['question_text']}\n\n"
                text_content += f"Answer {qa['question_num']}:\n{qa['answer_text']}\n\n"
                text_content += "-------------------------------------------\n\n"
            
            # Create the HTTP response for text file
            response = HttpResponse(text_content, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="{history.subject}_questions.txt"'
            
            return response
            
        # Handle PDF format export (default)
        else:
            # Render HTML template
            html_string = render_to_string('export_pdf.html', {
                'subject': history.subject,
                'questions_answers': questions_answers,
                'difficulty': history.difficulty,
                'date': history.created_at
            })
            
            # Try to use WeasyPrint for PDF generation
            try:
                # Check if GTK+ is properly installed on Windows
                import os
                if os.name == 'nt':  # Windows
                    # Try to import cairo which is an essential dependency for WeasyPrint on Windows
                    try:
                        import cairo
                    except ImportError:
                        # If cairo is missing, suggest TXT format and provide detailed installation instructions
                        messages.error(request, 
                            "PDF generation requires additional libraries on Windows. "
                            "Please use TXT format instead or follow the WeasyPrint installation guide: "
                            "https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows")
                        return redirect(request.path_info + '?format=txt')
                
                # Import weasyprint and attempt PDF generation
                import weasyprint
                pdf_file = BytesIO()
                weasyprint.HTML(string=html_string).write_pdf(pdf_file)
                pdf_file.seek(0)
                
                # Create the HTTP response with appropriate headers
                response = HttpResponse(pdf_file, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{history.subject}_questions.pdf"'
                
                return response
                
            except ImportError:
                messages.error(request, 
                    "WeasyPrint is not installed. Please install it with: pip install weasyprint "
                    "or use the TXT format export option instead.")
                # Redirect to the same URL but with txt format
                return redirect(request.path_info + '?format=txt')
            except Exception as pdf_error:
                # Log the specific error for debugging
                print(f"PDF Generation Error: {str(pdf_error)}")
                messages.error(request, 
                    f"Could not generate PDF: {str(pdf_error)}. "
                    f"Please use TXT format instead or see installation instructions at: "
                    f"https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows")
                # Redirect to the same URL but with txt format
                return redirect(request.path_info + '?format=txt')
        
    except ExamHistory.DoesNotExist:
        messages.error(request, 'Exam history not found')
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f'Error exporting questions: {str(e)}')
        return redirect('dashboard')

def connection_limit(request):
    """
    View to display when maximum database connections have been reached
    """
    return render(request, 'connection_limit.html')


def about(request):
    """
    View to display the about page
    """
    return render(request, 'about.html')

def features(request):
    """
    View to display the features page with different SmartExam features
    """
    return render(request, 'features.html')

def pricing(request):
    """
    View to display the pricing plans and subscription options
    """
    return render(request, 'pricing.html')

def support(request):
    """
    View to display the support page with FAQs and help resources
    """
    return render(request, 'support.html')

def contact(request):
    """
    View to handle the contact form submission and display the contact page
    """
    if request.method == 'POST':
        # Process contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        try:
            # Send email notification
            from django.core.mail import send_mail
            
            email_subject = f"Contact Form: {subject}"
            email_body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
            
            send_mail(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            
            # Return success message
            messages.success(request, "Thank you! Your message has been sent. We'll respond as soon as possible.")
            return redirect('contact')
            
        except Exception as e:
            messages.error(request, f"Sorry, there was an error sending your message: {str(e)}")
    
    return render(request, 'contact.html')
