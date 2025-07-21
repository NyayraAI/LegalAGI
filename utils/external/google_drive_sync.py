from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pathlib import Path
import os


class DriveSync:
    def __init__(self, folder_id):
        self.folder_id = folder_id
        self.service = self._authenticate()

    def _authenticate(self):
        SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
        creds = None
        token_path = Path("token.json")
        creds_path = Path("credentials.json")

        # 1. Try to load existing token
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        # 2. If no valid creds, do OAuth flow or refresh
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Try to refresh the token
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"[WARN] Token refresh failed: {e}")
                    creds = None  # Will trigger browser flow below
            if not creds or not creds.valid:
                # Browser login as last resort
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(creds_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the new token for next time
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        return build("drive", "v3", credentials=creds)

    def download_new_pdfs(self, download_dir="data/raw_pdfs"):
        download_path = Path(download_dir)

        results = (
            self.service.files()
            .list(
                q=f"'{self.folder_id}' in parents and mimeType='application/pdf'",
                fields="files(id, name, modifiedTime)",
            )
            .execute()
        )

        new_files = []
        for file in results.get("files", []):
            local_path = download_path / file["name"]
            if not local_path.exists():
                request = self.service.files().get_media(fileId=file["id"])
                with open(local_path, "wb") as f:
                    f.write(request.execute())
                new_files.append(file["name"])
                print(f"Downloaded: {file['name']}")

        return new_files
