"""Test cases for the Mergington High School API"""

import pytest
from fastapi import status


class TestGetActivities:
    """Test cases for GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        
        assert response.status_code == status.HTTP_200_OK
        activities = response.json()
        
        # Verify we have all expected activities
        assert len(activities) == 9
        assert "Debate Team" in activities
        assert "Science Club" in activities
        assert "Basketball Team" in activities
        assert "Tennis Club" in activities
        assert "Drama Club" in activities
        assert "Art Studio" in activities
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
        
    def test_activity_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)


class TestSignupForActivity:
    """Test cases for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        email = "newstudent@mergington.edu"
        activity_name = "Debate Team"
        
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]
        
    def test_signup_duplicate(self, client):
        """Test signing up when already registered"""
        email = "alex@mergington.edu"  # Already in Debate Team
        activity_name = "Debate Team"
        
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"
        
    def test_signup_activity_not_found(self, client):
        """Test signing up for non-existent activity"""
        email = "student@mergington.edu"
        activity_name = "Non Existent Activity"
        
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Activity not found"
        
    def test_signup_activity_full(self, client):
        """Test signing up when activity is at max capacity"""
        activity_name = "Chess Club"
        
        # First, get current participants count
        activities_response = client.get("/activities")
        activities = activities_response.json()
        chess_club = activities[activity_name]
        
        # Fill up remaining spots
        spots_left = chess_club["max_participants"] - len(chess_club["participants"])
        for i in range(spots_left):
            email = f"student{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            assert response.status_code == status.HTTP_200_OK
        
        # Try to add one more (should fail)
        email = "overflow@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"] == "Activity is full"
        
    def test_signup_with_special_characters_in_name(self, client):
        """Test signup with URL encoded activity name"""
        email = "student@mergington.edu"
        activity_name = "Art Studio"
        
        # URL encode the activity name
        from urllib.parse import quote
        encoded_name = quote(activity_name)
        
        response = client.post(
            f"/activities/{encoded_name}/signup?email={email}"
        )
        
        assert response.status_code == status.HTTP_200_OK


class TestUnregisterFromActivity:
    """Test cases for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "alex@mergington.edu"  # Already in Debate Team
        activity_name = "Debate Team"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Unregistered {email} from {activity_name}"
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]
        
    def test_unregister_not_registered(self, client):
        """Test unregistering when not registered for activity"""
        email = "notsignedup@mergington.edu"
        activity_name = "Debate Team"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"] == "Student is not signed up for this activity"
        
    def test_unregister_activity_not_found(self, client):
        """Test unregistering from non-existent activity"""
        email = "student@mergington.edu"
        activity_name = "Non Existent Activity"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Activity not found"


class TestRootEndpoint:
    """Test cases for root endpoint"""
    
    def test_root_redirects(self, client):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == "/static/index.html"


class TestEndToEndWorkflow:
    """Test complete user workflows"""
    
    def test_complete_signup_and_unregister_workflow(self, client):
        """Test signing up and then unregistering"""
        email = "workflow@mergington.edu"
        activity_name = "Programming Class"
        
        # Get initial state
        initial_response = client.get("/activities")
        initial_activities = initial_response.json()
        initial_count = len(initial_activities[activity_name]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert signup_response.status_code == status.HTTP_200_OK
        
        # Verify added
        after_signup = client.get("/activities")
        after_signup_activities = after_signup.json()
        assert len(after_signup_activities[activity_name]["participants"]) == initial_count + 1
        assert email in after_signup_activities[activity_name]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert unregister_response.status_code == status.HTTP_200_OK
        
        # Verify removed
        after_unregister = client.get("/activities")
        after_unregister_activities = after_unregister.json()
        assert len(after_unregister_activities[activity_name]["participants"]) == initial_count
        assert email not in after_unregister_activities[activity_name]["participants"]
        
    def test_multiple_signups_different_activities(self, client):
        """Test that a student can sign up for multiple different activities"""
        email = "multi@mergington.edu"
        activities = ["Debate Team", "Science Club", "Basketball Team"]
        
        for activity_name in activities:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            assert response.status_code == status.HTTP_200_OK
        
        # Verify student is in all activities
        all_activities = client.get("/activities").json()
        for activity_name in activities:
            assert email in all_activities[activity_name]["participants"]
