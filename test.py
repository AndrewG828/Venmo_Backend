import unittest
from app import hash_password, verify_password
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestPasswordHashing(unittest.TestCase):

    def setUp(self):
        # Test setup if needed
        self.salt = os.getenv("PASSWORD_SALT").encode('utf-8')
        self.iterations = int(os.getenv("NUMBER_OF_ITERATIONS"))
        self.test_password = "test_password"
        self.test_password_hashed = hash_password(self.test_password)

    def test_hash_password_consistency(self):
        # Check if hashing the same password results in the same hash
        hashed1 = hash_password(self.test_password)
        hashed2 = hash_password(self.test_password)
        self.assertEqual(hashed1, hashed2, "Hashing should be consistent for the same input.")

    def test_hash_password_uniqueness(self):
        # Check if hashing different passwords results in different hashes
        another_password = "another_password"
        hashed_another = hash_password(another_password)
        self.assertNotEqual(self.test_password_hashed, hashed_another, 
                            "Hashes should be unique for different passwords.")

    def test_verify_password_success(self):
        # Verify that the correct password matches the stored hash
        self.assertTrue(verify_password(self.test_password_hashed, self.test_password),
                        "Correct password should pass verification.")

    def test_verify_password_failure(self):
        # Verify that an incorrect password does not match the stored hash
        wrong_password = "wrong_password"
        self.assertFalse(verify_password(self.test_password_hashed, wrong_password),
                         "Incorrect password should not pass verification.")
    
    def test_same_password_hashing(self):
        # Verify that an incorrect password does not match the stored hash
        password1 = "JameCunning123"
        password2 = "JameCunning123"
        self.assertTrue(hash_password(password1)==hash_password(password2))

if __name__ == "__main__":
    unittest.main()
