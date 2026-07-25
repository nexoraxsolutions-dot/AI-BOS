import LoginForm from '../../components/LoginForm'

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto flex max-w-6xl items-center justify-center">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="mt-4 text-4xl font-semibold">Welcome back</h1>
            <p className="mt-2 text-slate-400">Sign in to your account to continue</p>
          </div>
          <LoginForm />
        </div>
      </div>
    </main>
  )
}