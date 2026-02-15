# StudyItUp - Frontend

A modern, interactive React-based frontend for an AI-powered study planning and learning assistant.

## Features

- 🎨 **Modern UI** - Built with React 18, TypeScript, and Tailwind CSS
- 🔐 **Authentication** - Secure JWT-based authentication with auto-refresh
- 📊 **Dashboard** - Comprehensive overview of study progress and stats
- 💬 **AI Chat** - Interactive learning chat with AI tutor
- 🧠 **Quiz System** - AI-generated quizzes with detailed results
- 📈 **Analytics** - Track progress and identify weak areas
- 📚 **Study Plans** - Create and manage personalized study plans
- 🎯 **Responsive Design** - Works seamlessly on desktop, tablet, and mobile

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **State Management**: Zustand
- **Routing**: React Router v6
- **Styling**: Tailwind CSS
- **Forms**: React Hook Form + Zod validation
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Notifications**: React Hot Toast

## Prerequisites

- Node.js 18+ and npm
- Backend API running (see backend README)

## Installation

1. **Install dependencies**
```bash
npm install
```

2. **Configure environment**
```bash
cp .env.example .env
```

Edit `.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_NAME=AI Study Planner
```

3. **Start development server**
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
src/
├── api/                    # API client and services
│   ├── client.ts          # Axios instance with interceptors
│   └── services.ts        # API service methods
├── components/            # React components
│   ├── ui/               # Reusable UI components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   └── Loading.tsx
│   └── layout/           # Layout components
│       └── Layout.tsx
├── pages/                # Page components
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   ├── DashboardPage.tsx
│   ├── ChatPage.tsx
│   └── QuizPage.tsx
├── stores/               # Zustand state stores
│   ├── authStore.ts
│   ├── studyPlanStore.ts
│   ├── chatStore.ts
│   └── quizStore.ts
├── types/                # TypeScript type definitions
│   └── index.ts
├── lib/                  # Utility functions
│   └── utils.ts
├── App.tsx              # Main app component with routing
├── main.tsx             # Entry point
└── index.css            # Global styles
```

## Key Features Implementation

### Authentication Flow

The app uses JWT-based authentication with automatic token refresh:

1. User logs in → Receives access & refresh tokens
2. Tokens stored in localStorage
3. Access token sent with every API request
4. On 401 error → Automatically refreshes token
5. On refresh failure → Redirects to login

### State Management

Uses Zustand for simple, performant state management:

- **authStore**: User authentication and profile
- **studyPlanStore**: Study plan CRUD operations
- **chatStore**: Chat sessions and messages
- **quizStore**: Quiz generation and submission

### API Integration

Axios client with interceptors handles:
- Automatic token injection
- Token refresh on expiry
- Error handling and toast notifications
- Request/response logging

### Form Validation

React Hook Form + Zod provides:
- Type-safe form validation
- Real-time error messages
- Easy form state management
- Schema-based validation

## Usage Examples

### Login
```typescript
const { login } = useAuthStore();
await login({ email, password });
```

### Generate Quiz
```typescript
const { generateQuiz } = useQuizStore();
await generateQuiz('Operating Systems', 'Computer Science', 10, 'medium');
```

### Send Chat Message
```typescript
const { sendMessage } = useChatStore();
await sendMessage('Explain process synchronization');
```

### Create Study Plan
```typescript
const { createPlan } = useStudyPlanStore();
await createPlan({
  exam_type: 'GATE_IT',
  target_date: '2025-02-01',
  daily_hours: 4,
  current_knowledge: {}
});
```

## Customization

### Theme Colors

Edit `tailwind.config.js` to customize colors:
```javascript
theme: {
  extend: {
    colors: {
      primary: 'your-color',
      // ...
    }
  }
}
```

### API Base URL

Change in `.env`:
```env
VITE_API_BASE_URL=https://your-api-domain.com
```

## Building for Production

```bash
npm run build
```

Output will be in `dist/` directory. Deploy to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- Any static hosting service

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_WS_URL` | WebSocket URL | `ws://localhost:8000` |
| `VITE_APP_NAME` | Application name | `AI Study Planner` |

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Code splitting for routes
- Lazy loading for heavy components
- Optimized bundle size
- Fast initial load time

## Troubleshooting

### API Connection Issues

1. Check backend is running
2. Verify `VITE_API_BASE_URL` in `.env`
3. Check browser console for errors
4. Verify CORS settings on backend

### Build Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Type Errors

```bash
# Regenerate TypeScript types
npm run build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Contact support

---

**Built with ❤️ using React + TypeScript + Vite**
