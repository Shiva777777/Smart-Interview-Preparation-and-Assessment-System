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

    recommendations = []
    
    for cat in categories:
        score = domain_scores[cat]
        # Recommend if score is below 70% or not attempted yet
        if score is None or score < 70.0:
            resource = RECOMMENDATION_RESOURCES.get(cat)
            if resource:
                recommendations.append({
                    'domain': cat,
                    'score': score, # None if not attempted
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
