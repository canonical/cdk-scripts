#!/bin/env python3

# from roadmap.sheets import Roadmap
from roadmap.gsheets import Roadmap
from roadmap.logging import Logger
from roadmap.trello import Utils

logger = Logger()
logger.set_level("debug")

roadmap = Roadmap(
    key="1eyah_MNJoULo8Y7XnzirXuOEDm9cuWsmkz25OLIJTGA",
    org="Cloud",
    team="Kubernetes",
    release="21.04",
)

roadmap_features = roadmap.get_features()


# Trello

TRELLO_BOARDS = ["TestBoard"]

api_secret = "1837d178896a175198bbe353690fe77435f77a7edbf770ce07fec568ceab9449"
api_key = "a0c7db3670669c24c6f0c16fbdb13024"

utils = Utils(api_key, api_secret, TRELLO_BOARDS)

# Cleanup
# utils.delete_all_cards("21.04")
# utils.blackhole_lists("21.04")

# Test
utils.create_release("21.04")

category_mapping = {
    "Quality/Release": "TestBoard",
    "Kubeflow": "TestBoard",
    "MicroK8s": "TestBoard",
    "Charmed Kubernetes": "TestBoard",
}

utils.create_feature_cards(roadmap_features, category_mapping)

trello_features = utils.get_feature_cards("21.04")

roadmap.update_features(trello_features)
