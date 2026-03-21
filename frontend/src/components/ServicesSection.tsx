import { motion } from "framer-motion";
import {
  Dumbbell,
  Apple,
  Calendar,
  Smartphone,
  MessageCircle,
  BookOpen,
  Pill,
  Stethoscope,
} from "lucide-react";

const services = [
  { icon: Dumbbell, title: "Treino Personalizado", desc: "Montado para seu objetivo, nível e rotina" },
  { icon: Apple, title: "Dieta Sob Medida", desc: "Plano alimentar adaptado ao seu dia a dia" },
  { icon: Calendar, title: "Organização de Rotina", desc: "Treino e dieta integrados à sua vida real" },
  { icon: Smartphone, title: "App MFIT", desc: "Acompanhe seus treinos pelo aplicativo" },
  { icon: MessageCircle, title: "Suporte WhatsApp", desc: "Canal aberto para comunicação direta" },
  { icon: BookOpen, title: "Material Educativo", desc: "Aprenda sobre treino, nutrição e saúde" },
  { icon: Pill, title: "Suplementação", desc: "Orientação personalizada de suplementos" },
  { icon: Stethoscope, title: "Indicação Médica", desc: "Rede de médicos para acompanhamento" },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

const item = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

const ServicesSection = () => {
  return (
    <section id="servicos" className="py-24 px-6 bg-gradient-dark">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <p className="text-primary text-sm tracking-[0.3em] mb-3 font-body uppercase">O que você recebe</p>
          <h2 className="text-4xl md:text-5xl font-display font-bold text-foreground">
            Tudo Incluso na <span className="text-gradient-gold">Consultoria</span>
          </h2>
        </motion.div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {services.map((s) => (
            <motion.div
              key={s.title}
              variants={item}
              className="bg-card border border-border rounded-sm p-6 hover:border-gold/30 transition-colors duration-300 group"
            >
              <s.icon className="w-8 h-8 text-primary mb-4 group-hover:text-gold-glow transition-colors" />
              <h3 className="font-display text-lg text-foreground mb-2">{s.title}</h3>
              <p className="text-muted-foreground text-sm font-body">{s.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default ServicesSection;
