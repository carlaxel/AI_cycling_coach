import pytest
from cycling_analyzer.reporter import _classify_session, SessionClassification
from cycling_analyzer.analyzer import AnalysisResult
from cycling_analyzer.models import WorkoutData, SessionSummary

def test_classify_session_endurance():
    session_data = SessionSummary(
        start_time=None,
        timer_time=3600.0,
        elapsed_time=3600.0,
        distance=30000.0,
        avg_power=180,
        max_power=400,
        avg_heart_rate=140,
        max_heart_rate=160,
        ascent=100.0,
        sub_sport="road",
        hr_zones=None
    )
    workout_data = WorkoutData(
        session=session_data,
        laps=[],
        records=[]
    )
    result = AnalysisResult(
        workout=workout_data,
        intensity_factor=0.75,
        tss=50.0,
        ftp=253,
        weight=95.0,
        variability_index=1.05
    )
    
    classification = _classify_session(result)
    assert classification.session_type == "Endurance"
    
def test_classify_session_recovery():
    session_data = SessionSummary(
        start_time=None,
        timer_time=3600.0,
        elapsed_time=3600.0,
        distance=20000.0,
        avg_power=120,
        max_power=200,
        avg_heart_rate=120,
        max_heart_rate=130,
        ascent=50.0,
        sub_sport="road",
        hr_zones=None
    )
    workout_data = WorkoutData(
        session=session_data,
        laps=[],
        records=[]
    )
    result = AnalysisResult(
        workout=workout_data,
        intensity_factor=0.55,
        tss=30.0,
        ftp=253,
        weight=95.0,
        variability_index=1.05
    )
    
    classification = _classify_session(result)
    assert classification.session_type == "Recovery"
