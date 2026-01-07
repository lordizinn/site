import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const SubscribePage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    name: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.email || !formData.name) {
      toast.error('Preencha todos os campos');
      return;
    }

    setLoading(true);
    
    try {
      const response = await axios.post(`${API_URL}/subscription/create-preference`, formData);
      const { preference_id, external_reference } = response.data;
      
      if (preference_id.startsWith('mock_')) {
        // Mock mode - simulate success
        toast.success('Modo de demonstração: Simulando pagamento aprovado');
        setTimeout(() => {
          navigate(`/subscription/success?ref=${external_reference}`);
        }, 2000);
      } else {
        // Redirect to Mercado Pago
        window.location.href = `https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=${preference_id}`;
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar assinatura');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-6">
      <Card className="w-full max-w-md bg-[#0A0A0A] border-[#1F1F22]">
        <CardHeader>
          <CardTitle className="text-2xl font-heading text-center">Assinar Aviator Analytics Pro</CardTitle>
          <CardDescription className="text-center text-[#A1A1AA]">
            Acesso completo ao sistema de análise estatística
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <div className="mb-6 p-4 bg-[#050505] border border-[#1F1F22] rounded-sm">
            <div className="flex justify-between items-center">
              <span className="text-[#A1A1AA]">Assinatura Mensal</span>
              <span className="text-2xl font-mono font-bold text-[#00FF94]">R$ 100,00</span>
            </div>
            <p className="text-xs text-[#52525B] mt-2">Renovação automática mensal</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name" className="text-[#EDEDED]">Nome Completo</Label>
              <Input
                id="name"
                data-testid="subscribe-name-input"
                type="text"
                placeholder="Seu nome"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="bg-[#050505] border-[#1F1F22] focus:border-[#00FF94] focus:ring-[#00FF94] text-[#EDEDED] placeholder:text-[#52525B] mt-2"
                required
              />
            </div>

            <div>
              <Label htmlFor="email" className="text-[#EDEDED]">Email</Label>
              <Input
                id="email"
                data-testid="subscribe-email-input"
                type="email"
                placeholder="seu@email.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="bg-[#050505] border-[#1F1F22] focus:border-[#00FF94] focus:ring-[#00FF94] text-[#EDEDED] placeholder:text-[#52525B] mt-2"
                required
              />
            </div>

            <Button
              data-testid="submit-subscription-button"
              type="submit"
              disabled={loading}
              className="w-full bg-[#00FF94] text-black font-bold hover:bg-[#00CC76] hover:shadow-[0_0_20px_rgba(0,255,148,0.4)] transition-all duration-300 rounded-sm uppercase tracking-wide py-6"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processando...
                </>
              ) : (
                'Prosseguir para Pagamento'
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => navigate('/')}
              className="text-sm text-[#A1A1AA] hover:text-[#EDEDED] transition-colors"
            >
              Voltar
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SubscribePage;