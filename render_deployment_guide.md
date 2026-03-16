# DreamVision Production Deployment Guide

This guide explains how to deploy your new **Express Node.js API** to Render (Free Tier) and your HTML Dashboard to **Netlify** (Free Tier).

## Part 1: Deploying the API to Render

1. First, make sure you push your codebase to GitHub (including the `express_backend` folder).
2. Go to [Render.com](https://render.com/) and create a free account.
3. Click **New +** and select **Web Service**.
4. Connect your GitHub account and select your `DreamVision` repository.
5. In the configuration settings, fill out the following:
   * **Root Directory**: `express_backend`
   * **Environment**: `Node`
   * **Build Command**: `npm install`
   * **Start Command**: `npm start`
6. Scroll down to **Environment Variables** and add the following key:
   * **Key**: `MONGO_URI`
   * **Value**: `mongodb+srv://harsh1:%23london%261234@harsh1.hfifgiu.mongodb.net/`
7. Click **Create Web Service**. 
8. Render will now build and deploy your API. Once finished, copy the provided URL (e.g., `https://dreamvision-api.onrender.com`).

---

## Part 2: Updating Frontend API URL

Before deploying the frontend, you must update `frontend/script.js` to point to your new live Render URL instead of `localhost`.

1. Open `frontend/script.js`.
2. Change line 1 from:
   ```javascript
   const API_BASE = "http://localhost:3000";
   ```
   To your new Render URL:
   ```javascript
   const API_BASE = "https://dreamvision-api.onrender.com";
   ```
3. Commit and push this change to GitHub.

---

## Part 3: Deploying Frontend to Netlify

1. Go to [Netlify.com](https://www.netlify.com/) and create a free account.
2. Click **Add new site** > **Import an existing project**.
3. Connect your GitHub account and select your `DreamVision` repository.
4. In the configuration settings, fill out the following:
   * **Base directory**: `frontend`
   * **Build command**: *(leave blank)*
   * **Publish directory**: `frontend`
5. Click **Deploy Site**.
6. Netlify will instantly publish your static HTML, CSS, and JS dashboard.

**Done!** The ESP32 will upload data through the Python `run_live_thermal.py` edge script straight to MongoDB, the Render API will pull it, and the Netlify Dashboard will visualize it from anywhere in the world!
