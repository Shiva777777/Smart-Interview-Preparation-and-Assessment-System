from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from quiz.models import QuizAttempt

# Curated reference list of recommended resources per technical domain
RECOMMENDATION_RESOURCES = {
    'Python': {
        'topics': ['Object Oriented Programming (OOP)', 'Decorators and Generators', 'Multithreading and AsyncIO', 'Memory Management / Garbage Collection'],
        'pdf_title': 'Advanced Python Reference Guide',
        'pdf_url': 'https://docs.python.org/3/tutorial/index.html',
        'video_title': 'Python Tutorial for Beginners (freeCodeCamp)',
        'video_url': 'https://www.youtube.com/watch?v=rfscVS0vtbw'
    },
    'DBMS': {
        'topics': ['Database Normalization (1NF, 2NF, 3NF, BCNF)', 'ACID Transactions & Concurrency Control', 'Database Indexing & B-Trees', 'SQL Query Execution Plans'],
        'pdf_title': 'DBMS Notes & System Concepts',
        'pdf_url': 'https://www.db-book.com/',
        'video_title': 'DBMS Complete Course (Gate Smashers)',
        'video_url': 'https://www.youtube.com/watch?v=ok5y3Y6C9V0'
    },
    'Operating System': {
        'topics': ['CPU Process Scheduling Algorithms', 'Deadlocks Detection and Prevention', 'Paging, Segmentation, and Virtual Memory', 'Process Synchronization & Semaphores'],
        'pdf_title': 'Operating Systems: Three Easy Pieces Reference',
        'pdf_url': 'https://pages.cs.wisc.edu/~remzi/OSTEP/',
        'video_title': 'Introduction to Operating Systems (Neso Academy)',
        'video_url': 'https://www.youtube.com/watch?v=vBURTt97EkA'
    },
    'Computer Networks': {
        'topics': ['OSI Layer Model & TCP/IP Stack', 'TCP vs UDP Transmission Protocols', 'IP Addressing, Subnetting, & CIDR', 'DNS, HTTP/HTTPS, and SSL Handshakes'],
        'pdf_title': 'Computer Networks Study Guide',
        'pdf_url': 'https://www.ietf.org/',
        'video_title': 'Computer Networking Course (freeCodeCamp)',
        'video_url': 'https://www.youtube.com/watch?v=IPvYjXofLQY'
    },
    'DevOps': {
        'topics': ['Docker Containerization & Image Layering', 'CI/CD Pipeline Configurations (Jenkins, GitHub Actions)', 'Infrastructure as Code (Terraform scripts)', 'Kubernetes Cluster Pods & Deployments'],
        'pdf_title': 'DevOps Engineering Handbook Summarized',
        'pdf_url': 'https://www.docker.com/resources/what-container',
        'video_title': 'DevOps Roadmap for Beginners (freeCodeCamp)',
        'video_url': 'https://www.youtube.com/watch?v=hQcFE0RD0cQ'
    },
    'SQL': {
        'topics': ['Outer/Inner/Self Joins', 'Grouping, Aggregates, & Having Clauses', 'Subqueries & Common Table Expressions (CTEs)', 'Window Functions (Row_Number, Rank, Dense_Rank)'],
        'pdf_title': 'SQL Query Syntax & Joins Cheat Sheet',
        'pdf_url': 'https://sqlzoo.net/',
        'video_title': 'SQL Tutorial for Beginners (Programming with Mosh)',
        'video_url': 'https://www.youtube.com/watch?v=HXTtJSQS15Y'
    },
    'Machine Learning': {
        'topics': ['Supervised vs Unsupervised Models', 'Overfitting mitigation & Bias-Variance tradeoff', 'Neural Networks Architecture basics', 'Validation metrics (ROC-AUC, Precision-Recall)'],
        'pdf_title': 'Introduction to Statistical Learning (ISLR PDF Book)',
        'pdf_url': 'https://www.statlearning.com/',
        'video_title': 'Machine Learning Course for Beginners (freeCodeCamp)',
        'video_url': 'https://www.youtube.com/watch?v=GwIo3gTOB3I'
    }
}

@login_required
def recommendation_view(request):
    quiz_attempts = QuizAttempt.objects.filter(user=request.user)
    
    # Calculate average score per domain
    categories = ['Python', 'DBMS', 'Operating System', 'Computer Networks', 'DevOps', 'SQL', 'Machine Learning']
    domain_scores = {}
    
    for cat in categories:
        cat_avg = quiz_attempts.filter(domain=cat).aggregate(Avg('score'))['score__avg']
        if cat_avg is not None:
            domain_scores[cat] = float(cat_avg)
        else:
            domain_scores[cat] = None # Not attempted yet

    import os
    from django.conf import settings
    import urllib.request
    import json

    api_key = os.environ.get('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', '')
    weak_domains = [cat for cat in categories if domain_scores[cat] is None or domain_scores[cat] < 70.0]
    
    recommendations = []
    if api_key and weak_domains:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
            prompt = (
                f"A candidate is preparing for interviews but is weak in the following topics/domains: {weak_domains}.\n\n"
                f"Suggest personalized learning resources for each weak domain. Return the result strictly as a JSON array where each object has these keys:\n"
                f"- 'domain': The domain name (must be one of: {weak_domains})\n"
                f"- 'topics': A list of 3-4 specific sub-topics they should focus on (list of strings)\n"
                f"- 'pdf_title': Title of a recommended study guide, article, or documentation (string)\n"
                f"- 'pdf_url': A valid link to that study guide or official documentation (string)\n"
                f"- 'video_title': Title of a recommended video tutorial or playlist (string)\n"
                f"- 'video_url': A valid YouTube link or educational video link (string)\n\n"
                f"Return ONLY the raw JSON array, without any markdown formatting or backticks."
            )
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'x-goog-api-key': api_key
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                text_response = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                
                if text_response.startswith("```"):
                    lines = text_response.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    text_response = "\n".join(lines).strip()
                
                recommendations = json.loads(text_response)
                # Map score back to recommendations
                for rec in recommendations:
                    rec['score'] = domain_scores.get(rec.get('domain'))
        except Exception as e:
            print(f"Gemini Recommendation failed: {str(e)}. Falling back to local resources.")
            recommendations = []

    # Fallback to local resources if Gemini fails or is not configured
    if not recommendations:
        for cat in categories:
            score = domain_scores[cat]
            if score is None or score < 70.0:
                resource = RECOMMENDATION_RESOURCES.get(cat)
                if resource:
                    recommendations.append({
                        'domain': cat,
                        'score': score,
                        'topics': resource['topics'],
                        'pdf_title': resource['pdf_title'],
                        'pdf_url': resource['pdf_url'],
                        'video_title': resource['video_title'],
                        'video_url': resource['video_url']
                    })

    return render(request, 'recommendation/display.html', {
        'recommendations': recommendations,
        'has_attempts': quiz_attempts.exists()
    })
