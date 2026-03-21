const Footer = () => {
  return (
    <footer className="py-8 px-6 border-t border-border">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <p className="font-display text-lg text-foreground tracking-wider">
          Carletti <span className="text-gradient-gold">Fit</span> — Team
        </p>
        <p className="text-muted-foreground text-xs font-body">
          © {new Date().getFullYear()} Carletti Fit. Todos os direitos reservados.
        </p>
      </div>
    </footer>
  );
};

export default Footer;
