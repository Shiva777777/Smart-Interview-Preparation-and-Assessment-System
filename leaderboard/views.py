from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from quiz.models import QuizAttempt
from coding.models import CodingAttempt

@login_required
def leaderboard_view(request):
    users = User.objects.all()
    rankings = []
    
    for u in users:
        # Quiz Aggregates
        q_stats = QuizAttempt.objects.filter(user=u).aggregate(
            avg_score=Avg('score'),
            total_quizzes=Count('id')
        )
        
        # Coding Aggregates
        c_stats = CodingAttempt.objects.filter(user=u, status='Passed').aggregate(
            total_solved=Count('id')
        )
        
        avg_score = q_stats['avg_score'] or 0.0
        total_quizzes = q_stats['total_quizzes'] or 0
        total_solved = c_stats['total_solved'] or 0
        
        # Calculate overall activity points to rank
        activity_points = (total_quizzes * 10) + (total_solved * 25)
        
        # Determine displayed name
        display_name = u.get_full_name().strip()
        if not display_name:
            display_name = u.username

        # Don't show users who haven't done anything to keep leaderboard clean
        if activity_points > 0:
            rankings.append({
                'name': display_name,
                'avg_score': round(avg_score, 1),
                'total_quizzes': total_quizzes,
                'total_solved': total_solved,
                'activity_points': activity_points
            })

    # Sort rankings by activity points descending
    rankings = sorted(rankings, key=lambda x: x['activity_points'], reverse=True)
    
    # Add ranks
    for index, rank in enumerate(rankings):
        rank['rank'] = index + 1

    return render(request, 'leaderboard/list.html', {
        'rankings': rankings
    })
