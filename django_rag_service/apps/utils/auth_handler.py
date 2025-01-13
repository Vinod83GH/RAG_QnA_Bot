import base64
from cryptography.fernet import Fernet
import hashlib

from django.conf import settings


class Authentication:
    """
    Secret key based authentication.
    """

    @staticmethod
    def get_auth_token(user_email=""):
        """
        Encrypt user email using a secret key and return the encrypted message.
        :param user_email:
        :return:
        """
        auth_secret_key = settings.SECRET_KEY

        # Hashing the string converts it into a fixed-length sequence of bytes (in this case, 32 bytes for SHA-256)
        # Fernet keys, need to be a specific length and format. Hashing ensures that the random string is converted
        # into a suitable format for use as a key
        hashed_key = hashlib.sha256(auth_secret_key.encode()).digest()

        # Encode the hashed key to make it URL-safe base64-encoded bytes
        fernet_key = base64.urlsafe_b64encode(hashed_key)

        # Use the key to create a Fernet instance
        cipher = Fernet(fernet_key)

        message = user_email.encode()
        encrypted_message = cipher.encrypt(message)
        encrypted_message = encrypted_message.decode()

        return encrypted_message
