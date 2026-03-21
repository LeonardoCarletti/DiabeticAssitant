import { motion } from "framer-motion";
import heroImage from "@/assets/hero-fitness.jpg";

const HeroSection = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Image */}
      <div className="absolute inset-0">
        <img
          src={heroImage}
          alt="Atleta treinando com iluminação dourada"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/80 via-background/60 to-background" />
        <div className="absolute inset-0 bg-gradient-to-r from-background/90 via-transparent to-background/90" />
      </div>

      {/* Content */}
      <div className="relative z-10 text-center px-6 max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <p className="text-primary font-body text-sm md:text-base tracking-[0.3em] mb-4 uppercase">
            Consultoria Online de Treinamento
          </p>
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-display font-bold leading-[0.9] mb-6">
            <span className="text-foreground">Carletti</span>{" "}
            <span className="text-gradient-gold">Fit</span>
            <br />
            <span className="text-foreground text-3xl md:text-5xl lg:text-6xl">— Team</span>
          </h1>
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="text-muted-foreground text-base md:text-lg max-w-2xl mx-auto mb-10 font-body leading-relaxed"
        >
          Treino personalizado, dieta sob medida e acompanhamento completo para
          transformar seu corpo e sua rotina — do iniciante ao atleta.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          <a
            href="#precos"
            className="bg-gradient-gold text-primary-foreground font-display text-lg tracking-wider px-10 py-4 rounded-sm hover:shadow-gold transition-all duration-300 uppercase"
          >
            Começar Agora
          </a>
          <a
            href="#servicos"
            className="border border-gold/30 text-foreground font-display text-lg tracking-wider px-10 py-4 rounded-sm hover:bg-primary/10 transition-all duration-300 uppercase"
          >
            Saiba Mais
          </a>
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        animate={{ y: [0, 10, 0] }}
        transition={{ repeat: Infinity, duration: 2 }}
      >
        <div className="w-6 h-10 border-2 border-primary/40 rounded-full flex justify-center pt-2">
          <div className="w-1.5 h-1.5 bg-primary rounded-full" />
        </div>
      </motion.div>
    </section>
  );
};

export default HeroSection;
