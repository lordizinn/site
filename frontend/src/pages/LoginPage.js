import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await login(formData.email, formData.password);

    if (result.success) {
      toast.success('Login realizado com sucesso!');
      navigate('/dashboard');
    } else {
      toast.error(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-6">
      <Card className="w-full max-w-md bg-[#0A0A0A] border-[#1F1F22]">
        <CardHeader>
          <CardTitle className="text-2xl font-heading text-center">Login</CardTitle>
          <CardDescription className="text-center text-[#A1A1AA]">
            Acesse seu dashboard de análises
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email" className="text-[#EDEDED]">Email</Label>
              <Input
                id="email"
                data-testid="login-email-input"
                type="email"
                placeholder="seu@email.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="bg-[#050505] border-[#1F1F22] focus:border-[#00FF94] focus:ring-[#00FF94] text-[#EDEDED] placeholder:text-[#52525B] mt-2"
                required
              />
            </div>

            <div>
              <Label htmlFor="password" className="text-[#EDEDED]">Senha</Label>
              <Input
                id="password"
                data-testid="login-password-input"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="bg-[#050505] border-[#1F1F22] focus:border-[#00FF94] focus:ring-[#00FF94] text-[#EDEDED] placeholder:text-[#52525B] mt-2"
                required
              />
            </div>

            <Button
              data-testid="login-submit-button"
              type="submit"
              disabled={loading}
              className="w-full bg-[#00FF94] text-black font-bold hover:bg-[#00CC76] hover:shadow-[0_0_20px_rgba(0,255,148,0.4)] transition-all duration-300 rounded-sm uppercase tracking-wide py-6"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Entrando...
                </>
              ) : (
                'Entrar'
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => navigate('/')}
              className="text-sm text-[#A1A1AA] hover:text-[#EDEDED] transition-colors"
            >
              Voltar para início
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage;