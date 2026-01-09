import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function SignupPage() {
    return (
        <div className="container mx-auto px-4 py-16 md:py-24 flex items-center justify-center min-h-[60vh]">
            <div className="w-full max-w-sm space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="text-center space-y-2">
                    <h1 className="text-3xl font-black uppercase tracking-tighter">Create Account</h1>
                    <p className="text-muted-foreground text-sm">Join us to get exclusive access and rewards.</p>
                </div>

                <form className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <Input
                            type="text"
                            placeholder="First Name"
                            className="h-11 rounded-none bg-transparent border-input focus-visible:ring-ring placeholder:text-muted-foreground/50"
                            required
                        />
                        <Input
                            type="text"
                            placeholder="Last Name"
                            className="h-11 rounded-none bg-transparent border-input focus-visible:ring-ring placeholder:text-muted-foreground/50"
                            required
                        />
                    </div>
                    <Input
                        type="email"
                        placeholder="Email"
                        className="h-11 rounded-none bg-transparent border-input focus-visible:ring-ring placeholder:text-muted-foreground/50"
                        required
                    />
                    <Input
                        type="password"
                        placeholder="Password"
                        className="h-11 rounded-none bg-transparent border-input focus-visible:ring-ring placeholder:text-muted-foreground/50"
                        required
                    />

                    <Button className="w-full h-11 rounded-none uppercase font-bold tracking-wider bg-primary text-primary-foreground hover:bg-primary/90">
                        Create Account
                    </Button>
                </form>

                <div className="text-center text-sm text-muted-foreground">
                    Already have an account?{' '}
                    <Link href="/login" className="text-primary font-medium hover:underline">
                        Sign in
                    </Link>
                </div>
            </div>
        </div>
    );
}
