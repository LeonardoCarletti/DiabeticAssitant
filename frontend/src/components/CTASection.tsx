import { motion } from "framer-motion";
import { MessageCircle, Instagram } from "lucide-react";

const CTASection = () => {
  return (
    <section id="contato" className="py-24 px-6">
      <div className="max-w-3xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
        >
          <h2 className="text-4xl md:text-6xl font-display font-bold text-foreground mb-6">
            Pronto para a <span className="text-gradient-gold">Transformação</span>?
          </h2>
          <p className="text-muted-foreground text-lg font-body mb-10 leading-relaxed">
            Entre em contato agora e comece sua jornada com a Carletti Fit - Team.
            Seu corpo, sua rotina, sua evolução.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-5">
            {/* WhatsApp */}
            <a
              href={`https://wa.me/5511988024265?text=${encodeURIComponent("Olá! Vi o site da Carletti Fit e quero saber mais sobre a consultoria online de treino. Pode me ajudar?")}`}
              target="_blank"
              rel="noopener noreferrer"
              className="group relative inline-flex items-center gap-3 bg-[#25D366] text-white font-display text-lg tracking-wider px-10 py-5 rounded-sm overflow-hidden transition-all duration-300 hover:shadow-[0_0_30px_-5px_rgba(37,211,102,0.5)] uppercase w-full sm:w-auto justify-center"
            >
              <span className="absolute inset-0 bg-[#128C7E] translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
              <MessageCircle className="w-6 h-6 relative z-10" />
              <span className="relative z-10">Falar no WhatsApp</span>
            </a>

            {/* Instagram */}
            <a
              href="https://www.instagram.com/DIABETICOIMORTAL"
              target="_blank"
              rel="noopener noreferrer"
              className="group relative inline-flex items-center gap-3 font-display text-lg tracking-wider px-10 py-5 rounded-sm overflow-hidden transition-all duration-300 uppercase w-full sm:w-auto justify-center text-white"
              style={{
                background: "linear-gradient(135deg, #833ab4, #fd1d1d, #fcb045)",
              }}
            >
              <span
                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                style={{
                  background: "linear-gradient(135deg, #5b2d8e, #c4161a, #d49535)",
                }}
              />
              <Instagram className="w-6 h-6 relative z-10" />
              <span className="relative z-10">@DIABETICOIMORTAL</span>
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default CTASection;
