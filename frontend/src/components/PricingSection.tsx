import { motion } from "framer-motion";
import { Check, Star } from "lucide-react";

const plans = [
  {
    name: "Mensal",
    price: "149,90",
    period: "/mês",
    features: ["Treino personalizado", "Dieta sob medida", "App MFIT", "Suporte WhatsApp"],
    highlight: false,
    whatsappMsg: "Olá! Tenho interesse no plano *Mensal* (R$ 149,90) da Carletti Fit. Gostaria de mais informações para começar!",
  },
  {
    name: "Trimestral",
    price: "399,90",
    period: "/3 meses",
    monthly: "R$ 133,30/mês",
    features: ["Tudo do mensal", "Feedbacks recorrentes", "Material educativo", "Organização de rotina"],
    highlight: true,
    whatsappMsg: "Olá! Tenho interesse no plano *Trimestral* (R$ 399,90) da Carletti Fit. Quero dar o próximo passo na minha evolução!",
  },
  {
    name: "Semestral",
    price: "729,90",
    period: "/6 meses",
    monthly: "R$ 121,65/mês",
    features: ["Tudo do trimestral", "Suplementação orientada", "Indicação médica", "Prioridade no suporte"],
    highlight: false,
    whatsappMsg: "Olá! Tenho interesse no plano *Semestral* (R$ 729,90) da Carletti Fit. Quero transformar meu corpo com comprometimento!",
  },
  {
    name: "Anual",
    price: "999,90",
    period: "/ano",
    monthly: "R$ 83,33/mês",
    features: ["Tudo do semestral", "Melhor custo-benefício", "Acompanhamento completo", "Acesso a extras exclusivos"],
    highlight: false,
    whatsappMsg: "Olá! Tenho interesse no plano *Anual* (R$ 999,90) da Carletti Fit. Quero o melhor custo-benefício para minha transformação!",
  },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, scale: 0.95 },
  show: { opacity: 1, scale: 1, transition: { duration: 0.5 } },
};

const PricingSection = () => {
  return (
    <section id="precos" className="py-24 px-6 bg-gradient-dark">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <p className="text-primary text-sm tracking-[0.3em] mb-3 font-body uppercase">Investimento</p>
          <h2 className="text-4xl md:text-5xl font-display font-bold text-foreground">
            Escolha Seu <span className="text-gradient-gold">Plano</span>
          </h2>
        </motion.div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {plans.map((plan) => (
            <motion.div
              key={plan.name}
              variants={item}
              className={`relative rounded-sm p-8 flex flex-col border transition-all duration-300 ${
                plan.highlight
                  ? "border-primary bg-card shadow-gold"
                  : "border-border bg-card hover:border-gold/30"
              }`}
            >
              {plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-gold text-primary-foreground text-xs font-display tracking-wider px-4 py-1 rounded-sm flex items-center gap-1">
                  <Star className="w-3 h-3" /> Popular
                </div>
              )}

              <h3 className="font-display text-2xl text-foreground mb-1">{plan.name}</h3>
              {plan.monthly && (
                <p className="text-primary text-xs font-body mb-4">{plan.monthly}</p>
              )}
              {!plan.monthly && <div className="mb-4" />}

              <div className="mb-6">
                <span className="text-foreground text-4xl font-display font-bold">R$ {plan.price}</span>
                <span className="text-muted-foreground text-sm font-body">{plan.period}</span>
              </div>

              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-muted-foreground font-body">
                    <Check className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>

              <a
                href={`https://wa.me/5511988024265?text=${encodeURIComponent(plan.whatsappMsg)}`}
                target="_blank"
                rel="noopener noreferrer"
                className={`text-center font-display tracking-wider py-3 rounded-sm transition-all duration-300 uppercase text-sm ${
                  plan.highlight
                    ? "bg-gradient-gold text-primary-foreground hover:shadow-gold"
                    : "border border-border text-foreground hover:border-primary hover:text-primary"
                }`}
              >
                Quero Este
              </a>
            </motion.div>
          ))}
        </motion.div>

        {/* Spreadsheets */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-16 text-center border border-border rounded-sm p-8 bg-card"
        >
          <h3 className="font-display text-2xl text-foreground mb-2">
            Planilhas de Treino para a <span className="text-gradient-gold">Comunidade</span>
          </h3>
          <p className="text-muted-foreground font-body text-sm max-w-xl mx-auto">
            Planilhas personalizadas e atualizadas a cada 2 meses, disponíveis por preços promocionais para toda a comunidade Carletti Fit.
          </p>
        </motion.div>
      </div>
    </section>
  );
};

export default PricingSection;
