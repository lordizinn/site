import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { TrendingUp, BarChart3, Bell, CheckCircle2, Activity } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#050505] text-[#EDEDED]">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-radial from-[#00FF94]/10 via-transparent to-transparent"></div>
        
        <nav className="relative z-10 container mx-auto px-6 py-6">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-heading font-bold tracking-tight">
              AVIATOR <span className="text-[#00FF94]">ANALYTICS</span>
            </h1>
            <Button 
              data-testid="login-button"
              onClick={() => navigate('/login')} 
              variant="ghost" 
              className="text-[#EDEDED] hover:text-[#00FF94] transition-colors"
            >
              Entrar
            </Button>
          </div>
        </nav>

        <div className="relative z-10 container mx-auto px-6 py-20 lg:py-32">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-block mb-6 px-4 py-2 bg-[#0A0A0A] border border-[#1F1F22] rounded-sm">
              <span className="text-xs uppercase tracking-widest text-[#00FF94]">Análise Estatística Profissional</span>
            </div>
            
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-heading font-bold tracking-tight mb-6">
              Domine o jogo com
              <span className="block text-[#00FF94] mt-2">dados em tempo real</span>
            </h2>
            
            <p className="text-lg sm:text-xl text-[#A1A1AA] mb-12 max-w-2xl mx-auto">
              Sistema avançado de análise estatística do Aviator. Decisões baseadas em dados, não em sorte.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button
                data-testid="subscribe-cta-button"
                onClick={() => navigate('/subscribe')}
                className="bg-[#00FF94] text-black font-bold hover:bg-[#00CC76] hover:shadow-[0_0_20px_rgba(0,255,148,0.4)] transition-all duration-300 rounded-sm uppercase tracking-wide px-8 py-6 text-lg"
              >
                Assinar Acesso
              </Button>
              <div className="text-sm text-[#A1A1AA]">
                <span className="font-mono text-2xl text-[#EDEDED] block mb-1">R$ 100,00</span>
                <span>por mês</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="container mx-auto px-6 py-20">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="bg-[#0A0A0A] border-[#1F1F22] p-6 hover:border-[#27272A] transition-colors">
            <div className="mb-4">
              <div className="w-12 h-12 bg-[#00FF94]/10 rounded-sm flex items-center justify-center">
                <TrendingUp className="text-[#00FF94]" size={24} />
              </div>
            </div>
            <h3 className="text-xl font-heading font-semibold mb-3">Gráficos em Tempo Real</h3>
            <p className="text-[#A1A1AA]">Visualize padrões e tendências com gráficos profissionais atualizados instantaneamente.</p>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F22] p-6 hover:border-[#27272A] transition-colors">
            <div className="mb-4">
              <div className="w-12 h-12 bg-[#00FF94]/10 rounded-sm flex items-center justify-center">
                <Bell className="text-[#00FF94]" size={24} />
              </div>
            </div>
            <h3 className="text-xl font-heading font-semibold mb-3">Alertas Inteligentes</h3>
            <p className="text-[#A1A1AA]">Receba notificações baseadas em análises estatísticas de padrões históricos.</p>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F22] p-6 hover:border-[#27272A] transition-colors">
            <div className="mb-4">
              <div className="w-12 h-12 bg-[#00FF94]/10 rounded-sm flex items-center justify-center">
                <BarChart3 className="text-[#00FF94]" size={24} />
              </div>
            </div>
            <h3 className="text-xl font-heading font-semibold mb-3">Métricas Detalhadas</h3>
            <p className="text-[#A1A1AA]">Análise completa de multiplicadores, frequências e probabilidades estatísticas.</p>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F22] p-6 hover:border-[#27272A] transition-colors">
            <div className="mb-4">
              <div className="w-12 h-12 bg-[#00FF94]/10 rounded-sm flex items-center justify-center">
                <CheckCircle2 className="text-[#00FF94]" size={24} />
              </div>
            </div>
            <h3 className="text-xl font-heading font-semibold mb-3">Validação de Cenários</h3>
            <p className="text-[#A1A1AA]">Histórico transparente de alertas com status de confirmação baseado em resultados reais.</p>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F22] p-6 hover:border-[#27272A] transition-colors">
            <div className="mb-4">
              <div className="w-12 h-12 bg-[#00FF94]/10 rounded-sm flex items-center justify-center">
                <Activity className="text-[#00FF94]" size={24} />
              </div>
            </div>
            <h3 className="text-xl font-heading font-semibold mb-3">Histórico Completo</h3>
            <p className="text-[#A1A1AA]">Acesso a registros históricos completos de multiplicadores e padrões identificados.</p>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F22] p-6 hover:border-[#27272A] transition-colors">
            <div className="mb-4">
              <div className="w-12 h-12 bg-[#00FF94]/10 rounded-sm flex items-center justify-center">
                <BarChart3 className="text-[#00FF94]" size={24} />
              </div>
            </div>
            <h3 className="text-xl font-heading font-semibold mb-3">Dashboard Premium</h3>
            <p className="text-[#A1A1AA]">Interface profissional estilo trading com todas as informações que você precisa.</p>
          </Card>
        </div>
      </div>

      {/* CTA Section */}
      <div className="container mx-auto px-6 py-20">
        <Card className="bg-[#0A0A0A] border-[#1F1F22] p-12 text-center">
          <h3 className="text-3xl font-heading font-bold mb-4">Pronto para começar?</h3>
          <p className="text-[#A1A1AA] mb-8 max-w-2xl mx-auto">
            Acesse análises estatísticas profissionais e tome decisões baseadas em dados reais.
          </p>
          <Button
            data-testid="subscribe-footer-button"
            onClick={() => navigate('/subscribe')}
            className="bg-[#00FF94] text-black font-bold hover:bg-[#00CC76] hover:shadow-[0_0_20px_rgba(0,255,148,0.4)] transition-all duration-300 rounded-sm uppercase tracking-wide px-8 py-6 text-lg"
          >
            Assinar por R$ 100/mês
          </Button>
        </Card>
      </div>

      {/* Footer */}
      <footer className="border-t border-[#1F1F22] py-8">
        <div className="container mx-auto px-6 text-center text-[#52525B] text-sm">
          <p>© 2025 Aviator Analytics Pro. Este sistema trabalha apenas com análise de dados históricos e probabilidades.</p>
          <p className="mt-2">Não prometemos ganhos. Jogue com responsabilidade.</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;