"""
Unit tests for behavioral feature extraction, rate calculations, and sliding window pruning.
"""

import time
from monitor.file_monitor import FileEvent
from features.feature_extractor import BehavioralFeatureExtractor


def test_empty_window_features():
    """Verify empty window produces zero rates without division errors."""
    extractor = BehavioralFeatureExtractor(window_seconds=5.0)
    features = extractor.extract_features()

    assert features["create_rate"] == 0.0
    assert features["modified_rate"] == 0.0
    assert features["rename_rate"] == 0.0
    assert features["delete_rate"] == 0.0
    assert features["operations_rate"] == 0.0
    assert features["directories_affected"] == 0
    assert features["activity_burst"] == 0.0


def test_rate_calculations():
    """Verify that multiple events in window calculate accurate per-second rates."""
    extractor = BehavioralFeatureExtractor(window_seconds=5.0)
    now = time.time()

    # Add 10 modify events and 5 rename events across 2 directories
    for i in range(10):
        extractor.add_event(
            FileEvent(
                timestamp=now - (i * 0.1),
                event_type="MODIFY",
                src_path=f"/test/dirA/f{i}.txt",
                dest_path=None,
                filename=f"f{i}.txt",
                directory="/test/dirA",
                is_directory=False,
            )
        )

    for i in range(5):
        extractor.add_event(
            FileEvent(
                timestamp=now - (i * 0.1),
                event_type="RENAME",
                src_path=f"/test/dirB/f{i}.txt",
                dest_path=f"/test/dirB/f{i}.txt.locked",
                filename=f"f{i}.txt",
                directory="/test/dirB",
                is_directory=False,
            )
        )

    features = extractor.extract_features(current_time=now)
    assert features["modified_rate"] == 2.0   # 10 events / 5 sec
    assert features["rename_rate"] == 1.0     # 5 events / 5 sec
    assert features["operations_rate"] == 3.0 # 15 events / 5 sec
    assert features["directories_affected"] == 2
    assert features["activity_burst"] >= 10.0 # All 15 events occurred within 1 second


def test_window_pruning():
    """Verify events older than the sliding window are pruned."""
    extractor = BehavioralFeatureExtractor(window_seconds=5.0)
    now = time.time()

    # Add an event that is 10 seconds old
    old_event = FileEvent(
        timestamp=now - 10.0,
        event_type="CREATE",
        src_path="/test/old.txt",
        dest_path=None,
        filename="old.txt",
        directory="/test",
        is_directory=False,
    )
    extractor.add_event(old_event)

    features = extractor.extract_features(current_time=now)
    assert features["create_rate"] == 0.0
    assert features["operations_rate"] == 0.0
