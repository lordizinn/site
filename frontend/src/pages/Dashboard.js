import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, Bell, CheckCircle2, XCircle, Activity, BarChart3, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const { logout, token } = useAuth();
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [validatedAlerts, setValidatedAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }

    const fetchData = async () => {
      try {
        const [statsRes, historyRes, alertsRes, validatedRes] = await Promise.all([
          axios.get(`${API_URL}/dashboard/stats`),
          axios.get(`${API_URL}/aviator/history`),
          axios.get(`${API_URL}/alerts/recent`),
          axios.get(`${API_URL}/alerts/validated`)
        ]);

        setStats(statsRes.data);
        setHistory(historyRes.data.history);
        setAlerts(alertsRes.data.alerts);
        setValidatedAlerts(validatedRes.data.validated_alerts);
      } catch (error) {
        toast.error('Erro ao carregar dados');
        if (error.response?.status === 401) {
          logout();
          navigate('/login');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [token, navigate, logout]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="text-[#00FF94] text-xl font-mono">Carregando...</div>
      </div>
    );
  }

  const chartData = history.slice(0, 30).reverse().map((item, index) => ({
    index,
    multiplier: item.multiplier
  }));

  const getRiskColor = (level) => {
    switch(level) {
      case 'high': return 'bg-[#FF3366] text-white';
      case 'medium': return 'bg-[#FFD600] text-black';
      case 'low': return 'bg-[#00FF94] text-black';
      default: return 'bg-[#52525B] text-white';
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-[#EDEDED]">
      {/* Header */}
      <div className="border-b border-[#1F1F22]">
        <div className="container mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-heading font-bold tracking-tight">
              AVIATOR <span className="text-[#00FF94]">ANALYTICS</span>
            </h1>
            <Button
              data-testid="logout-button"
              onClick={logout}
              variant="ghost"
              className="text-[#A1A1AA] hover:text-[#EDEDED]"
            >
              Sair
            </Button>
          </div>
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="container mx-auto px-6 py-8" data-testid="dashboard-content">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="bg-[#0A0A0A] border-[#1F1F22]">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-[#A1A1AA] uppercase tracking-widest font-normal">Taxa de Confirmação</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-mono font-bold text-[#00FF94]">{stats?.confirmation_rate}%</div>
              <p className="text-xs text-[#52525B] mt-1">Cenários confirmados</p>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F22]">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-[#A1A1AA] uppercase tracking-widest font-normal">Total de Alertas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-mono font-bold text-[#EDEDED]">{stats?.total_alerts_issued}</div>
              <p className="text-xs text-[#52525B] mt-1">Alertas emitidos</p>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F22]">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-[#A1A1AA] uppercase tracking-widest font-normal">Multiplicadores Altos</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-mono font-bold text-[#00B8FF]">{stats?.high_multipliers_today}</div>
              <p className="text-xs text-[#52525B] mt-1">Hoje (>10x)</p>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F22]">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-[#A1A1AA] uppercase tracking-widest font-normal">Média Atual</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-mono font-bold text-[#EDEDED]">{stats?.avg_multiplier}x</div>
              <p className="text-xs text-[#52525B] mt-1">Multiplicador médio</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Chart */}
        <Card className="bg-[#0A0A0A] border-[#1F1F22] mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="text-[#00FF94]" size={20} />
              Gráfico de Multiplicadores em Tempo Real
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorMultiplier" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00FF94" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#00FF94" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F1F22" />
                <XAxis dataKey="index" stroke="#52525B" />
                <YAxis stroke="#52525B" />
                <Tooltip 
                  contentStyle={{ background: '#0A0A0A', border: '1px solid #1F1F22', borderRadius: '4px' }}
                  labelStyle={{ color: '#A1A1AA' }}
                  itemStyle={{ color: '#00FF94' }}
                />
                <Area type="monotone" dataKey="multiplier" stroke="#00FF94" strokeWidth={2} fillOpacity={1} fill="url(#colorMultiplier)" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Alerts and Validations Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Alerts */}
          <Card className="bg-[#0A0A0A] border-[#1F1F22]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="text-[#00FF94]" size={20} />
                Alertas Recentes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {alerts.map((alert) => (
                  <div key={alert.id} className="p-4 bg-[#050505] border border-[#1F1F22] rounded-sm hover:border-[#27272A] transition-colors">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-semibold text-[#EDEDED]">{alert.type}</span>
                      <Badge className={`${getRiskColor(alert.risk_level)} text-xs uppercase`}>
                        {alert.risk_level}
                      </Badge>
                    </div>
                    <div className="flex justify-between text-xs text-[#A1A1AA]">
                      <span>Limite: <span className="font-mono text-[#00FF94]">{alert.multiplier_threshold}x</span></span>
                      <span>Prob: <span className="font-mono">{alert.probability}%</span></span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Validated Alerts */}
          <Card className="bg-[#0A0A0A] border-[#1F1F22]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="text-[#00FF94]" size={20} />
                Histórico de Validações
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {validatedAlerts.map((alert) => (
                  <div key={alert.id} className="p-4 bg-[#050505] border border-[#1F1F22] rounded-sm hover:border-[#27272A] transition-colors">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-[#EDEDED]">{alert.status}</span>
                      {alert.confirmed ? (
                        <CheckCircle2 className="text-[#00FF94]" size={18} />
                      ) : (
                        <XCircle className="text-[#FF3366]" size={18} />
                      )}
                    </div>
                    <div className="flex justify-between text-xs text-[#A1A1AA]">
                      <span>Previsto: <span className="font-mono">{alert.predicted_multiplier}x</span></span>
                      <span>Real: <span className="font-mono">{alert.actual_multiplier}x</span></span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;