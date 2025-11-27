# 📐 Project Blueprint: YOTG Media Bot

**Status:** Draft / Active Development
**Target Python Version:** 3.12+
**Framework:** Aiogram 3.x
**License:** MIT

---

## 1. Executive Summary

**YOTG Media Bot** (Yet Another Media Downloader Helper TG Bot) is an asynchronous Telegram bot designed to fetch and deliver media content (audio/video) from public social platforms.

**Core Philosophy:**
1.  **Speed:** Minimized latency between request and delivery.
2.  **UX First:** Clean interface, informative progress updates, and correct metadata (covers, tags).
3.  **Privacy & Legal:** No retention of user data or downloaded media. Strict adherence to fair use policies.

---

## 2. Technical Architecture

### 2.1. Tech Stack
* **Language:** Python 3.13 (utilizing modern async features).
* **Bot Framework:** [Aiogram 3.x](https://docs.aiogram.dev/en/latest/) (Official Bot API).
* **Media Extraction:** `yt-dlp` (running via `asyncio` subprocesses/threads).
* **Database:** `aiosqlite` (SQLite) for user settings (language, quality presets) and limited usage stats. No storage of media links history.
* **Caching (Optional/Future):** `Redis` for caching file_ids to avoid re-uploading popular content.

### 2.2. High-Level Data Flow

1.  **Ingestion:** User sends a link (Private Chat) OR calls Inline Query.
2.  **Validation:**
    * `Middleware` checks if the user is not banned.
    * `Validator` checks if the URL is supported (YouTube, Spotify, X, IG).
3.  **Processing (The "Heavy Lifting"):**
    * Bot sends "Typing..." or "Uploading..." action.
    * `Downloader Service` invokes `yt-dlp` to extract metadata and download media to a TMPFS.
    * **Audio Post-processing:** Conversion to MP3/M4A, embedding thumbnail and ID3 tags (Artist, Title).
4.  **Delivery:**
    * Bot uploads the file to Telegram servers.
    * Bot obtains a `file_id` (for potential caching).
5.  **Cleanup:**
    * **Crucial:** The local file is immediately deleted from the server disk to ensure privacy and save space.

---

## 3. Functional Requirements

### 3.1. Supported Platforms (Phased Rollout)
* **Phase 1 (MVP):** YouTube Music.
* **Phase 2:** Spotify (Metadata bridging: search Spotify track on YouTube -> download).
* **Phase 3:** Twitter (X) & Instagram (Reels/Posts).
* **Phase 4:** TikTok & Twitch clips.

### 3.2. Interaction Modes
1.  **Direct Message (DM):**
    * User sends a link -> Bot replies with media.
    * Command `/start` - Greeting and legal disclaimer.
    * Command `/help` - Supported services list.
    * Command `/settings` - Audio quality (128/320kbps), Language.
2.  **Inline Mode:**
    * User types `@botname query` -> Bot searches YouTube -> User clicks result -> Audio is sent.
3.  **Group Chat:**
    * Bot listens for links (if admin/enabled) or explicit commands.
