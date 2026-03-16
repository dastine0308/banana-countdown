# Frontend — Banana Countdown

Built with **Next.js 14**, **TypeScript**, and **Tailwind CSS**.

## Setup

```bash
npm install
npm run dev
# → http://localhost:3000
```

Make sure the Flask backend is running on `http://localhost:5000` before starting the frontend.
The `next.config.js` proxies all `/api/*` requests to Flask automatically.

## Structure

```
frontend/
├── app/
│   ├── layout.tsx       # Root layout + metadata
│   ├── page.tsx         # Main page: upload flow + state management
│   └── globals.css      # Design tokens, fonts, animations
├── components/
│   ├── Header.tsx       # Top nav bar
│   ├── Uploader.tsx     # Drag-and-drop image upload zone
│   └── ResultCard.tsx   # Annotated image + detection cards
├── next.config.js       # API proxy to Flask
├── tailwind.config.ts
└── tsconfig.json
```

## Environment Variables

For production, set the backend URL via env var:

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://your-flask-server:5000
```

Then update `next.config.js` to use `process.env.NEXT_PUBLIC_API_URL`.
