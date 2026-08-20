from ui.training_screen import TrainingScreen


def test_training_exercises_have_distinct_targets():
    assert TrainingScreen._target_for_exercise("left_right", 0) == (-0.5, 0)
    assert TrainingScreen._target_for_exercise("left_right", 3) == (0.5, 0)
    assert TrainingScreen._target_for_exercise("front_back", 0) == (0, -0.45)
    assert TrainingScreen._target_for_exercise("front_back", 3) == (0, 0.45)
    assert TrainingScreen._target_for_exercise("center", 10) == (0, 0)


def test_moving_and_limit_targets_stay_inside_workspace():
    for elapsed in (0, 1, 10, 100):
        moving = TrainingScreen._target_for_exercise("moving", elapsed)
        limits = TrainingScreen._target_for_exercise("limits", elapsed)
        assert abs(moving[0]) <= 0.45 and abs(moving[1]) <= 0.35
        assert abs(limits[0]) <= 0.55 and abs(limits[1]) <= 0.55
