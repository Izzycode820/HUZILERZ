# SaaS Theme Management Rules (STRICT)

**Location:** `c:\S.T.E.V.E\V2\HUZILERZ\themes\`

This folder contains **React/Next.js applications** that serve strictly as **themes** for the SaaS platform. They are NOT independent projects while they live here.

## 🚨 THE GOLDEN RULE 🚨
**NEVER RUN `git init` INSIDE ANY FOLDER HERE.**
*   **Detailed Explanation:** The `HUZILERZ` folder is already a Git repository. Creating another git repository inside it (nested repo) breaks tracking and creates "empty folder" bugs in deployment.

---

## 1. What belongs here?
*   **Strictly Themes**: Only frontend code (UI/Design) for specific SaaS themes (e.g., `sneakers`, `merchflow`).
*   **No Features**: Do not build complex backend features here. These apps consume the SaaS API.
*   **React/Next.js**: These are standard Next.js applications acting as templates.

## 2. How to Add a New Theme
When you want to create a new theme (e.g., `booksstore`):

1.  Open your terminal in `HUZILERZ/themes/`.
2.  Run your creation command:
    ```bash
    npx create-next-app@latest bookstore
    ```
3.  **IMMEDIATELY AFTER CREATION:**
    *   Check if a `.git` folder was created inside `themes/bookstore/`.
    *   **DELETE IT.**
    *   Command to delete (PowerShell): `Remove-Item -Path themes/bookstore/.git -Recurse -Force`
4.  Only then can you run `git add .` from the main `HUZILERZ` folder.

## 3. How to Save Your Work (Daily)
*   **Always** run git commands from the root `HUZILERZ` folder.
*   ✅ **CORRECT:**
    ```bash
    cd c:\S.T.E.V.E\V2\HUZILERZ
    git add .
    git commit -m "Updated visuals on sneakers theme"
    git push
    ```
*   ❌ **WRONG:**
    ```bash
    cd themes/sneakers
    git add .  <-- This might look like it works, but pushing from root is safer.
    git commit <-- NEVER init a new repo here.
    ```

## 4. How to Make a Theme "Public"
If you finish a theme and want to share it (e.g., open source it, sell it independently):

1.  **Do NOT** touch the folder inside `HUZILERZ`.
2.  **Copy** the theme folder (e.g., `themes/sneakers`) to a separate location (e.g., your Desktop).
3.  Open that **copy** in VS Code.
4.  Run `git init` inside the **copy**.
5.  Push the **copy** to its own new repository.

---

**Summary:** 
*   **HUZILERZ** is the Master.
*   **Themes** are just folders inside the Master.
*   **Never** give a Theme its own Git brain (no `.git` folder).
