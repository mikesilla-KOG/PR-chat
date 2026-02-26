# PR-chat - Streamlit Cloud Deployment

This repository can be deployed to Streamlit Cloud in the same way as SermonsKB.

## Files included for deployment

- `pr_chat.db` (SQLite database with transcripts/chunks) **or** allow the app to initialize the database at startup and ingest sample documents.
- `faiss_index.faiss` (FAISS index for semantic search)
- `embeddings_meta.json` (metadata mapping chunks to documents)
- `data/transcripts/` and `data/uploads/` as needed (optional but handy for persistence)

You may choose to commit the database and index files to the repository or rebuild them at startup using the provided scripts. For small deployments you can simply check them in; for larger datasets you may want a build step.

## Streamlit Cloud setup

1. Go to https://share.streamlit.io/ and sign in with GitHub.
2. Click "New app".
3. Select:
   - Repository: `mikesilla-KOG/PR-chat`
   - Branch: `main` (or whichever branch you wish to deploy)
   - Main file path: `app/streamlit_app.py`
4. Click "Advanced settings".
   - Add any secrets you need (e.g. `OPENAI_API_KEY`).
   - You can also set environment variables such as you might in `.env`.
5. Click "Deploy".

Streamlit Cloud will install dependencies from `requirements.txt` and start the application. It will run the same code as you tested locally.

## Environment variables / secrets

Use the "Secrets" section to set the following if needed:

```
OPENAI_API_KEY = "sk-..."        # optional; required for AI chat
LOCAL_WHISPER_MODEL = "base"     # choose model size
DB_PATH = "pr_chat.db"          # location of the SQLite database
FAISS_INDEX_PATH = "faiss_index.faiss"
EMBEDDINGS_META = "embeddings_meta.json"
UPLOADS_DIR = "data/uploads"
TRANSCRIPTS_DIR = "data/transcripts"
```

## Optional initialization steps

If you do **not** commit the database/index files, the app will create an empty DB on startup. You can then:

```bash
streamlit run app/streamlit_app.py    # locally to prepare files
python scripts/ingest.py <your file>
python scripts/build_embeddings.py
```

and then commit the resulting `pr_chat.db` and FAISS files to the repo before pushing to Streamlit Cloud.

Alternatively, you can create a GitHub action or manual step to run these scripts automatically.

## Using Netlify / Other Services

Streamlit Cloud is the primary deployment target; Netlify or Vercel are not designed to run Python/Streamlit apps. If you truly need a static front end, consider converting the UI or deploying via Docker on a VPS.

## Notes

- Streamlit Cloud provides up to 1 GB of disk storage and a 24‑hour idle timeout on free tier. Keep your database size modest or use an external store if you need more persistence.
- The app’s root directory is writable, so uploaded files persist between restarts while the app is active.

Happy deploying! Your PR-chat chat interface will run live on a site just like SermonsKB’s `https://sermonskb.streamlit.app/`.