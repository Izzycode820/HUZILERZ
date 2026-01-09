import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function LoginPage() {
    return (
        <div className="container mx-auto px-4 py-16 md:py-24 flex items-center justify-center min-h-[60vh]">
            <div className="w-full max-w-sm space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="text-center space-y-2">
                    <h1 className="text-3xl font-black uppercase tracking-tighter">Login</h1>
                    <p className="text-muted-foreground text-sm">Enter your email and password to access your account.</p>
                </div>

                <form className="space-y-4" action={async (formData) => {
                    'use server'
                    // Handle login logic in real app
                }}>
                    <div className="space-y-2">
                        <Input
                            type="email"
                            placeholder="Email"
                            className="h-11 rounded-none bg-transparent border-input focus-visible:ring-ring placeholder:text-muted-foreground/50"
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <Input
                            type="password"
                            placeholder="Password"
                            className="h-11 rounded-none bg-transparent border-input focus-visible:ring-ring placeholder:text-muted-foreground/50"
                            required
                        />
                        <div className="text-right">
                            <Link href="/forgot-password" className="text-xs text-muted-foreground hover:text-primary hover:underline transition-colors">
                                Forgot password?
                            </Link>
                        </div>
                    </div>

                    <Button className="w-full h-11 rounded-none uppercase font-bold tracking-wider bg-primary text-primary-foreground hover:bg-primary/90">
                        Sign In
                    </Button>
                </form>

                <div className="text-center text-sm text-muted-foreground">
                    Don't have an account?{' '}
                    <Link href="/signup" className="text-primary font-medium hover:underline">
                        Create one
                    </Link>
                </div>
            </div>
        </div>
    );
}
