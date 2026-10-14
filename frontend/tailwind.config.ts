import type { Config } from 'tailwindcss';

export default <Partial<Config>>{
  theme: {
    extend: {
      fontFamily: {
        sans: ['Montserrat', 'Arial', 'sans-serif'],
      },
      colors: {
        primary: {
          DEFAULT: '#EB5F46',
          hover: '#c94a32',
          light: '#fff0ed',
        },
        navy: {
          DEFAULT: '#0D436C',
          dark: '#22223C',
        },
      },
    },
  },
};
