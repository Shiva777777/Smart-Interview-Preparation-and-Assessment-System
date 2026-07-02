import os
import sys
import tempfile
import subprocess
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
from .models import CodingQuestion, CodingAttempt

# Default coding problems to ensure immediate system runnability
DEFAULT_CODING_QUESTIONS = [
    {
        'title': 'Reverse a String',
        'description': 'Write a program that takes a string from standard input and prints its reversed representation to standard output.',
        'input_format': 'A single line containing a string S.',
        'output_format': 'Print the reversed string.',
        'sample_input': 'hello',
        'sample_output': 'olleh',
        'difficulty': 'Easy',
        'test_cases': [
            {'input': 'hello', 'output': 'olleh'},
            {'input': 'Django', 'output': 'ognajD'},
            {'input': '12345', 'output': '54321'},
            {'input': 'a', 'output': 'a'}
        ]
    },
    {
        'title': 'Palindrome Checker',
        'description': 'Write a program that checks if an input string is a palindrome. Case-sensitive. Print "YES" if it is a palindrome, otherwise print "NO".',
        'input_format': 'A single line containing a string S.',
        'output_format': 'YES or NO.',
        'sample_input': 'radar',
        'sample_output': 'YES',
        'difficulty': 'Easy',
        'test_cases': [
            {'input': 'radar', 'output': 'YES'},
            {'input': 'hello', 'output': 'NO'},
            {'input': 'Level', 'output': 'NO'}, # Case sensitive
            {'input': 'racecar', 'output': 'YES'}
        ]
    },
    {
        'title': 'Fibonacci Series',
        'description': 'Write a program that prints the first N Fibonacci numbers separated by space. The sequence starts with 0 and 1.',
        'input_format': 'An integer N representing the count of numbers.',
        'output_format': 'N space-separated integers.',
        'sample_input': '5',
        'sample_output': '0 1 1 2 3',
        'difficulty': 'Medium',
        'test_cases': [
            {'input': '5', 'output': '0 1 1 2 3'},
            {'input': '1', 'output': '0'},
            {'input': '2', 'output': '0 1'},
            {'input': '8', 'output': '0 1 1 2 3 5 8 13'}
        ]
    },
    {
        'title': 'Factorial Calculator',
        'description': 'Write a program that calculates and prints the factorial of a non-negative integer N.',
        'input_format': 'A single non-negative integer N.',
        'output_format': 'The factorial value of N.',
        'sample_input': '5',
        'sample_output': '120',
        'difficulty': 'Medium',
        'test_cases': [
            {'input': '5', 'output': '120'},
            {'input': '0', 'output': '1'},
            {'input': '1', 'output': '1'},
            {'input': '7', 'output': '5040'}
        ]
    }
]

def run_code_sandbox(code, stdin_input):
    """Executes python code locally with input redirection and timeout."""
    # Create temporary file inside working directory
    temp_fd, temp_path = tempfile.mkstemp(suffix='.py', dir=os.getcwd())
    try:
        with os.fdopen(temp_fd, 'w') as f:
            f.write(code)
            
        res = subprocess.run(
            [sys.executable, temp_path],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=2.0
        )
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout: Execution exceeded 2.0 seconds limits."
    except Exception as e:
        return -1, "", f"Execution error: {str(e)}"
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

@login_required
def coding_home_view(request):
    # Check if user domain is non-tech/non-programming
    is_tech = False
    profile = request.user.profile
    domain = (profile.preferred_domain or "").lower()
    goal = (profile.career_goal or "").lower()
    
    tech_keywords = ['python', 'django', 'devops', 'software', 'data science', 'machine learning', 'backend', 'frontend', 'web development', 'it', 'computer', 'coder', 'developer', 'programmer', 'coding', 'tech']
    if not domain or any(kw in domain for kw in tech_keywords) or any(kw in goal for kw in tech_keywords):
        is_tech = True
        
    if not is_tech:
        return render(request, 'coding/non_tech_info.html', {
            'domain': profile.preferred_domain,
            'career_goal': profile.career_goal or "Professional"
        })

    # Seed default questions if table is empty
    if not CodingQuestion.objects.exists():
        for q_data in DEFAULT_CODING_QUESTIONS:
            CodingQuestion.objects.create(**q_data)

    questions = CodingQuestion.objects.all()
    user_attempts = CodingAttempt.objects.filter(user=request.user)
    completed_q_ids = set(user_attempts.filter(status='Passed').values_list('question_id', flat=True))

    return render(request, 'coding/home.html', {
        'questions': questions,
        'completed_q_ids': completed_q_ids
    })

@login_required
def coding_session_view(request, question_id):
    question = get_object_or_404(CodingQuestion, id=question_id)
    
    # Python template code starter
    boilerplate = (
        "import sys\n\n"
        "def solve():\n"
        "    # Read inputs from stdin\n"
        "    input_data = sys.stdin.read().strip()\n"
        "    \n"
        "    # Write your solution here\n"
        "    # output = ...\n"
        "    # print(output)\n"
        "    pass\n\n"
        "if __name__ == '__main__':\n"
        "    solve()\n"
    )
    
    return render(request, 'coding/session.html', {
        'question': question,
        'boilerplate': boilerplate
    })

@login_required
def coding_run_view(request, question_id):
    if request.method == 'POST':
        question = get_object_or_404(CodingQuestion, id=question_id)
        data = json.loads(request.body)
        code = data.get('code', '')
        custom_input = data.get('custom_input', question.sample_input)

        code_status, stdout, stderr = run_code_sandbox(code, custom_input)
        
        return JsonResponse({
            'status': 'success',
            'exit_code': code_status,
            'stdout': stdout,
            'stderr': stderr
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def coding_submit_view(request, question_id):
    if request.method == 'POST':
        question = get_object_or_404(CodingQuestion, id=question_id)
        data = json.loads(request.body)
        code = data.get('code', '')

        test_cases = question.test_cases
        passed_count = 0
        total_cases = len(test_cases)
        
        error_msg = ""
        compilation_failed = False

        for tc in test_cases:
            tc_input = tc['input']
            tc_expected = tc['output'].strip()
            
            exit_code, stdout, stderr = run_code_sandbox(code, tc_input)
            
            if exit_code != 0:
                compilation_failed = True
                error_msg = stderr or "Execution Error"
                break
                
            if stdout.strip() == tc_expected:
                passed_count += 1
            else:
                # Store output mismatch if any for logging
                error_msg = f"Expected: '{tc_expected}', Got: '{stdout.strip()}'"

        # Score marks
        marks = int((passed_count / total_cases) * 100) if total_cases > 0 else 0
        status = "Passed" if passed_count == total_cases else ("Compilation Error" if compilation_failed else "Failed")

        # Save coding attempt
        CodingAttempt.objects.create(
            user=request.user,
            question=question,
            code=code,
            status=status,
            marks=marks
        )

        return JsonResponse({
            'status': 'success',
            'run_status': status,
            'passed': passed_count,
            'total': total_cases,
            'marks': marks,
            'error_message': error_msg
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
