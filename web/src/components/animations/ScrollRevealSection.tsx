import React, { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { cn } from '../../lib/utils';

interface Props {
  id?: string;
  title?: string;
  className?: string;
  children: React.ReactNode;
  delay?: number;
}

export function ScrollRevealSection({ id, title, className, children, delay = 0.1 }: Props) {
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.section
      ref={ref}
      id={id}
      className={cn("py-12 relative scroll-mt-24", className)}
      initial={{ opacity: 0, y: 15 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 15 }}
      transition={{ duration: 0.6, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      {title && (
        <h2 className="text-3xl tracking-tight font-bold text-slate-900 mb-8 border-b pb-4 border-slate-100">{title}</h2>
      )}
      {children}
    </motion.section>
  );
}
