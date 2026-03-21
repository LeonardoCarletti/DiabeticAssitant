import { motion } from "framer-motion";

const methods = [
  "Low Volume",
  "Upper / Lower",
  "PPL UL",
  "Full Body",
  "ABC",
  "ABCDE",
];

const goals = [
  "Emagrecimento",
  "Melhoria Estética",
  "Fisiculturismo / Bodybuilding",
  "Treino para Luta",
  "Fortalecimento",
  "Hipertrofia",
];

const audiences = [
  "Crianças",
  "Jovens",
  "Adultos",
  "Mulheres",
  "Homens",
  "Idosos",
];

const TagCloud = ({ items, delay = 0 }: { items: string[]; delay?: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ duration: 0.6, delay }}
    className="flex flex-wrap justify-center gap-3"
  >
    {items.map((t) => (
      <span
        key={t}
        className="border border-border bg-secondary/50 text-foreground px-5 py-2.5 rounded-sm text-sm font-body tracking-wide hover:border-gold/40 hover:bg-primary/10 transition-all duration-300 cursor-default"
      >
        {t}
      </span>
    ))}
  </motion.div>
);

const MethodsSection = () => {
  return (
    <section className="py-24 px-6">
      <div className="max-w-4xl mx-auto space-y-20">
        {/* Methods */}
        <div className="text-center">
          <p className="text-primary text-sm tracking-[0.3em] mb-3 font-body uppercase">Metodologias</p>
          <h2 className="text-4xl md:text-5xl font-display font-bold text-foreground mb-8">
            Métodos de <span className="text-gradient-gold">Treino</span>
          </h2>
          <TagCloud items={methods} />
        </div>

        {/* Goals */}
        <div className="text-center">
          <p className="text-primary text-sm tracking-[0.3em] mb-3 font-body uppercase">Objetivos</p>
          <h2 className="text-4xl md:text-5xl font-display font-bold text-foreground mb-8">
            Para Cada <span className="text-gradient-gold">Objetivo</span>
          </h2>
          <TagCloud items={goals} delay={0.1} />
        </div>

        {/* Audiences */}
        <div className="text-center">
          <p className="text-primary text-sm tracking-[0.3em] mb-3 font-body uppercase">Público</p>
          <h2 className="text-4xl md:text-5xl font-display font-bold text-foreground mb-8">
            Para <span className="text-gradient-gold">Todos</span>
          </h2>
          <TagCloud items={audiences} delay={0.2} />
        </div>
      </div>
    </section>
  );
};

export default MethodsSection;
