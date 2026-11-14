# Inventory Forecast Dashboard

A Streamlit dashboard for inventory demand forecasts, stock status, store analysis, and CSV exports.

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository and add the files in this folder to its root.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
3. Select **Create app**, choose your repository and `main` branch, and set **Main file path** to `app.py`.
4. In **Advanced settings**, choose Python **3.11**, then deploy.
5. After the app starts, copy the `*.streamlit.app` URL and share it.

The repository must contain `app.py`, `requirements.txt`, and `inventory_model_bundle.joblib` together in the root folder. The model is about 49 MB; use Git or GitHub Desktop to add it rather than the GitHub browser uploader.

## Sharing note

If you want anyone with the link to open the dashboard, make the GitHub repository and Streamlit app public. This also makes the Python source and saved model publicly accessible. If you want restricted access, keep the repository/app private and invite viewers in Streamlit Community Cloud.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```
