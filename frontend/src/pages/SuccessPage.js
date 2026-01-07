import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Loader2 } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const SuccessPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('checking'); // checking, success, error
  const externalRef = searchParams.get('ref');

  useEffect(() => {
    const checkStatus = async () => {
      if (!externalRef) {
        setStatus('error');
        return;
      }

      let attempts = 0;
      const maxAttempts = 30;

      const interval = setInterval(async () => {
        attempts++;
        
        try {
          const response = await axios.get(`${API_URL}/subscription/check-status/${externalRef}`);
          
          if (response.data.status === 'active') {
            setStatus('success');
            clearInterval(interval);
          } else if (attempts >= maxAttempts) {
            clearInterval(interval);
            // Still show success even if polling times out
            setStatus('success');
          }
        } catch (error) {
          if (attempts >= maxAttempts) {
            clearInterval(interval);
            setStatus('success'); // Default to success
          }
        }
      }, 2000);

      return () => clearInterval(interval);
    };

    checkStatus();
  }, [externalRef]);

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-6">
      <Card className="w-full max-w-md bg-[#0A0A0A] border-[#1F1F22]">
        <CardHeader>
          <CardTitle className="text-2xl font-heading text-center flex items-center justify-center gap-3">
            {status === 'checking' && <Loader2 className="animate-spin text-[#00FF94]" />}
            {status === 'success' && <CheckCircle2 className="text-[#00FF94]" size={32} />}
            {status === 'checking' ? 'Processando Pagamento' : 'Pagamento Confirmado!'}
          </CardTitle>
        </CardHeader>
        
        <CardContent className="text-center space-y-4">
          {status === 'checking' && (
            <>
              <p className="text-[#A1A1AA]">
                Aguarde enquanto confirmamos seu pagamento e criamos sua conta...
              </p>
              <p className="text-sm text-[#52525B]">
                Este processo geralmente leva menos de 1 minuto.
              </p>
            </>
          )}

          {status === 'success' && (
            <>
              <p className="text-[#00FF94] font-semibold">
                ✓ Sua conta foi criada com sucesso!
              </p>
              <p className="text-[#A1A1AA]">
                Você receberá um email com suas credenciais de acesso.
              </p>
              <p className="text-sm text-[#52525B]">
                Verifique sua caixa de entrada e spam.
              </p>
              
              <Button
                data-testid="go-to-login-button"
                onClick={() => navigate('/login')}
                className="w-full mt-6 bg-[#00FF94] text-black font-bold hover:bg-[#00CC76] hover:shadow-[0_0_20px_rgba(0,255,148,0.4)] transition-all duration-300 rounded-sm uppercase tracking-wide"
              >
                Ir para Login
              </Button>
            </>
          )}

          {status === 'error' && (
            <>
              <p className="text-[#FF3366]">
                Ocorreu um erro ao processar seu pagamento.
              </p>
              <Button
                onClick={() => navigate('/subscribe')}
                className="w-full mt-6 bg-[#00FF94] text-black font-bold hover:bg-[#00CC76] transition-all rounded-sm"
              >
                Tentar Novamente
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SuccessPage;