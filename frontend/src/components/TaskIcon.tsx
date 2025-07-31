import React from 'react';
import { 
  BookOpen, 
  Image, 
  Smartphone, 
  Code, 
  Database, 
  Globe, 
  Search, 
  FileText, 
  Settings, 
  Download, 
  Upload, 
  Monitor, 
  Users, 
  Mail, 
  Calendar, 
  ShoppingCart, 
  DollarSign, 
  BarChart, 
  PieChart, 
  Camera, 
  Music, 
  Video, 
  Headphones,
  Cpu,
  Server,
  Cloud,
  Lock,
  Shield,
  Key,
  Wifi,
  Bluetooth,
  Map,
  Navigation,
  Compass,
  Clock,
  Timer,
  Alarm,
  Bell,
  MessageSquare,
  Phone,
  Printer,
  Scan,
  Eye,
  EyeOff,
  Edit,
  Trash2,
  Save,
  FolderPlus,
  FileX,
  Scissors,
  Copy,
  Paste,
  Undo,
  Redo,
  RefreshCw,
  PlayCircle,
  PauseCircle,
  StopCircle,
  SkipForward,
  SkipBack,
  Volume2,
  VolumeX,
  Zap,
  Command,
  Terminal,
  Target,
  Flag,
  CheckSquare,
  Briefcase,
  Lightbulb,
  Rocket,
  Star,
  Award,
  Activity,
  TrendingUp,
  Calculator,
  Layers,
  Package,

  Wrench,
  Cog,
  Hash,
  GitBranch,
  Folder,
  FilePlus,
  HardDrive,
  Wifi4,
  Router,
  Smartphone2,
  Tablet,
  Laptop,
  PcCase,
  Component,
  Microchip,
  MemoryStick,
  HardDriveIcon,
  ScanLine,
  Workflow,
  Puzzle,
  Building,
  Home,
  MapPin,
  Route,
  Send,
  Share2,
  LinkIcon,
  Archive,
  Box,
  Container,
  Grid3x3,
  Layout,
  Maximize,
  Minimize,
  RotateCcw,
  RotateCw,
  Shuffle,
  Repeat,
  PlayIcon,
  PauseIcon,
  StopIcon,
  SkipBackIcon,
  SkipForwardIcon,
  FastForward,
  Rewind,
  Volume,
  VolumeDown,
  VolumeUp,
  Mic,
  MicOff,
  Headphones2,
  Speaker,
  Radio,
  Disc,
  Music2,
  Music3,
  Music4,
  AudioLines,
  Waveform
} from 'lucide-react';

export interface TaskIconProps {
  type: string;
  size?: 'small' | 'medium' | 'large';
  className?: string;
  showProgress?: boolean;
  progressValue?: number; // 0-100
  isActive?: boolean;
  isCompleted?: boolean;
}

export const TaskIcon: React.FC<TaskIconProps> = React.memo(({ 
  type, 
  size = 'medium', 
  className = '',
  showProgress = false,
  progressValue = 0,
  isActive = false,
  isCompleted = false
}) => {
  // Log para debugging
  console.log(`🎯 [TaskIcon] Rendering icon for task with progress: ${progressValue}%, active: ${isActive}, completed: ${isCompleted}`);
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-5 h-5',
    large: 'w-6 h-6'
  };

  const iconClass = `${sizeClasses[size]} ${className}`;

  // Array of task-related icons for variety
  const taskIcons = [
    Target, Flag, CheckSquare, Briefcase, Lightbulb, Rocket, 
    Star, Award, Activity, TrendingUp, Calculator, Layers,
    Package, Wrench, Wrench, Cog, Hash, GitBranch, Folder,
    FilePlus, Workflow, Puzzle, Building, Archive, Box,
    Grid3x3, Layout, Send, Share2, LinkIcon, Component
  ];

  const getIcon = (taskType: string) => {
    const normalizedType = taskType.toLowerCase();

    // 🎯 NUEVO: Mapeo directo de iconos del backend LLM
    // Si el taskType es exactamente un nombre de icono válido, usar mapeo directo
    const directIconMapping: { [key: string]: React.ReactElement } = {
      // Desarrollo/Programación
      'code': <Code className={iconClass} />,
      'database': <Database className={iconClass} />,
      'terminal': <Terminal className={iconClass} />,
      'server': <Server className={iconClass} />,
      
      // Lugares/Mapas
      'map': <Map className={iconClass} />,
      'navigation': <Navigation className={iconClass} />,
      'compass': <Compass className={iconClass} />,
      'globe': <Globe className={iconClass} />,
      
      // Documentos/Archivos
      'file': <FileText className={iconClass} />,
      'book': <BookOpen className={iconClass} />,
      'edit': <Edit className={iconClass} />,
      'folder': <Folder className={iconClass} />,
      
      // Análisis/Datos
      'chart': <BarChart className={iconClass} />,
      'calculator': <Calculator className={iconClass} />,
      'activity': <Activity className={iconClass} />,
      'grid': <Grid3x3 className={iconClass} />,
      
      // Búsqueda/Investigación
      'search': <Search className={iconClass} />,
      
      // Creatividad/Diseño
      'image': <Image className={iconClass} />,
      'lightbulb': <Lightbulb className={iconClass} />,
      'star': <Star className={iconClass} />,
      'camera': <Camera className={iconClass} />,
      
      // Comunicación
      'message': <MessageSquare className={iconClass} />,
      'mail': <Mail className={iconClass} />,
      'send': <Send className={iconClass} />,
      'phone': <Phone className={iconClass} />,
      
      // Negocios/Comercial
      'briefcase': <Briefcase className={iconClass} />,
      'dollar': <DollarSign className={iconClass} />,
      'building': <Building className={iconClass} />,
      'users': <Users className={iconClass} />,
      
      // Multimedia
      'music': <Music className={iconClass} />,
      'video': <Video className={iconClass} />,
      'mic': <Mic className={iconClass} />,
      'headphones': <Headphones className={iconClass} />,
      
      // Herramientas/Utilidades
      'wrench': <Wrench className={iconClass} />,
      'settings': <Settings className={iconClass} />,
      'package': <Package className={iconClass} />,
      'workflow': <Workflow className={iconClass} />,
      
      // Genérico
      'target': <Target className={iconClass} />,
      'flag': <Flag className={iconClass} />,
      'rocket': <Rocket className={iconClass} />,
      'zap': <Zap className={iconClass} />
    };

    // 🎯 PRIORIDAD 1: Si es un mapeo directo de icono del LLM, usarlo
    if (directIconMapping[normalizedType]) {
      console.log(`🎯 Direct icon mapping used: ${normalizedType}`);
      return directIconMapping[normalizedType];
    }

    // 🎯 PRIORIDAD 2: Lógica heurística para compatibilidad con títulos de tareas
    // Lectura y escritura
    if (normalizedType.includes('lectura') || normalizedType.includes('leer') || 
        normalizedType.includes('escribir') || normalizedType.includes('redactar') ||
        normalizedType.includes('documento') || normalizedType.includes('texto')) {
      return <BookOpen className={iconClass} />;
    }

    // Imágenes y diseño
    if (normalizedType.includes('imagen') || normalizedType.includes('diseño') || 
        normalizedType.includes('grafico') || normalizedType.includes('visual') ||
        normalizedType.includes('foto') || normalizedType.includes('picture')) {
      return <Image className={iconClass} />;
    }

    // Aplicaciones
    if (normalizedType.includes('app') || normalizedType.includes('aplicacion') || 
        normalizedType.includes('aplicación') || normalizedType.includes('software') ||
        normalizedType.includes('mobile') || normalizedType.includes('movil')) {
      return <Smartphone className={iconClass} />;
    }

    // Programación y código
    if (normalizedType.includes('codigo') || normalizedType.includes('código') || 
        normalizedType.includes('programar') || normalizedType.includes('desarrollar') ||
        normalizedType.includes('script') || normalizedType.includes('function')) {
      return <Code className={iconClass} />;
    }

    // Base de datos
    if (normalizedType.includes('base') || normalizedType.includes('datos') || 
        normalizedType.includes('database') || normalizedType.includes('sql') ||
        normalizedType.includes('mongodb') || normalizedType.includes('mysql')) {
      return <Database className={iconClass} />;
    }

    // Web y navegación
    if (normalizedType.includes('web') || normalizedType.includes('sitio') || 
        normalizedType.includes('página') || normalizedType.includes('pagina') ||
        normalizedType.includes('navegador') || normalizedType.includes('http')) {
      return <Globe className={iconClass} />;
    }

    // Búsqueda
    if (normalizedType.includes('buscar') || normalizedType.includes('search') || 
        normalizedType.includes('encontrar') || normalizedType.includes('investigar')) {
      return <Search className={iconClass} />;
    }

    // Archivos
    if (normalizedType.includes('archivo') || normalizedType.includes('file') || 
        normalizedType.includes('documento') || normalizedType.includes('folder') ||
        normalizedType.includes('carpeta')) {
      return <FileText className={iconClass} />;
    }

    // Configuración
    if (normalizedType.includes('configurar') || normalizedType.includes('config') || 
        normalizedType.includes('ajustar') || normalizedType.includes('settings') ||
        normalizedType.includes('opciones')) {
      return <Settings className={iconClass} />;
    }

    // Descargas
    if (normalizedType.includes('descargar') || normalizedType.includes('download') || 
        normalizedType.includes('bajar')) {
      return <Download className={iconClass} />;
    }

    // Uploads/Subidas
    if (normalizedType.includes('subir') || normalizedType.includes('upload') || 
        normalizedType.includes('cargar')) {
      return <Upload className={iconClass} />;
    }

    // Sistemas y servidores
    if (normalizedType.includes('sistema') || normalizedType.includes('servidor') || 
        normalizedType.includes('server') || normalizedType.includes('servicio')) {
      return <Server className={iconClass} />;
    }

    // Cloud/Nube
    if (normalizedType.includes('nube') || normalizedType.includes('cloud') || 
        normalizedType.includes('remoto')) {
      return <Cloud className={iconClass} />;
    }

    // Seguridad
    if (normalizedType.includes('seguridad') || normalizedType.includes('security') || 
        normalizedType.includes('proteger') || normalizedType.includes('cifrar')) {
      return <Shield className={iconClass} />;
    }

    // Autenticación
    if (normalizedType.includes('login') || normalizedType.includes('auth') || 
        normalizedType.includes('autenticar') || normalizedType.includes('password') ||
        normalizedType.includes('contraseña')) {
      return <Key className={iconClass} />;
    }

    // Audio
    if (normalizedType.includes('audio') || normalizedType.includes('sonido') || 
        normalizedType.includes('música') || normalizedType.includes('music')) {
      return <Music className={iconClass} />;
    }

    // Video
    if (normalizedType.includes('video') || normalizedType.includes('pelicula') || 
        normalizedType.includes('película') || normalizedType.includes('reproducir')) {
      return <Video className={iconClass} />;
    }

    // Comunicación
    if (normalizedType.includes('mensaje') || normalizedType.includes('chat') || 
        normalizedType.includes('comunicar') || normalizedType.includes('enviar')) {
      return <MessageSquare className={iconClass} />;
    }

    // Email
    if (normalizedType.includes('email') || normalizedType.includes('correo') || 
        normalizedType.includes('mail')) {
      return <Mail className={iconClass} />;
    }

    // Análisis y reportes
    if (normalizedType.includes('analizar') || normalizedType.includes('reporte') || 
        normalizedType.includes('estadistica') || normalizedType.includes('chart')) {
      return <BarChart className={iconClass} />;
    }

    // Ventas y comercio
    if (normalizedType.includes('venta') || normalizedType.includes('comercio') || 
        normalizedType.includes('tienda') || normalizedType.includes('shop')) {
      return <ShoppingCart className={iconClass} />;
    }

    // Dinero y finanzas
    if (normalizedType.includes('dinero') || normalizedType.includes('precio') || 
        normalizedType.includes('pago') || normalizedType.includes('financial')) {
      return <DollarSign className={iconClass} />;
    }

    // Tiempo y calendario
    if (normalizedType.includes('tiempo') || normalizedType.includes('fecha') || 
        normalizedType.includes('calendario') || normalizedType.includes('cita')) {
      return <Calendar className={iconClass} />;
    }

    // Usuarios y personas
    if (normalizedType.includes('usuario') || normalizedType.includes('user') || 
        normalizedType.includes('persona') || normalizedType.includes('cliente')) {
      return <Users className={iconClass} />;
    }

    // Monitor y pantalla
    if (normalizedType.includes('pantalla') || normalizedType.includes('monitor') || 
        normalizedType.includes('display') || normalizedType.includes('mostrar')) {
      return <Monitor className={iconClass} />;
    }

    // Terminal y comandos
    if (normalizedType.includes('terminal') || normalizedType.includes('comando') || 
        normalizedType.includes('shell') || normalizedType.includes('bash')) {
      return <Terminal className={iconClass} />;
    }

    // Energía y rendimiento
    if (normalizedType.includes('optimizar') || normalizedType.includes('rendimiento') || 
        normalizedType.includes('performance') || normalizedType.includes('velocidad')) {
      return <Zap className={iconClass} />;
    }

    // Para tareas generales, usar un icono aleatorio basado en el título
    const taskHash = taskType.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const IconComponent = taskIcons[taskHash % taskIcons.length];
    return <IconComponent className={iconClass} />;
  };

  const icon = getIcon(type);

  // If no progress indicator needed, return simple icon with proper styling
  if (!showProgress) {
    return React.cloneElement(icon, {
      className: `${iconClass} ${
        isCompleted ? 'text-green-300' : 
        isActive ? 'text-white' : 
        'text-gray-300'
      } ${isActive ? 'opacity-100' : 'opacity-70'}`
    });
  }

  // Mejoramos el tamaño y la visibilidad del círculo de progreso
  const progressSizes = {
    small: { svg: 'w-10 h-10', icon: 'w-4 h-4', radius: 16, strokeWidth: 3 },
    medium: { svg: 'w-12 h-12', icon: 'w-5 h-5', radius: 18, strokeWidth: 3.5 },
    large: { svg: 'w-14 h-14', icon: 'w-6 h-6', radius: 20, strokeWidth: 4 }
  };

  const progressSize = progressSizes[size];
  const circumference = 2 * Math.PI * progressSize.radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (progressValue / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center">
      {/* Círculo de progreso */}
      <svg 
        className={`${progressSize.svg} transform rotate-[-90deg]`}
        viewBox={`0 0 ${(progressSize.radius + progressSize.strokeWidth) * 2} ${(progressSize.radius + progressSize.strokeWidth) * 2}`}
      >
        {/* Background circle */}
        <circle
          cx={progressSize.radius + progressSize.strokeWidth}
          cy={progressSize.radius + progressSize.strokeWidth}
          r={progressSize.radius}
          fill="transparent"
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth={progressSize.strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={progressSize.radius + progressSize.strokeWidth}
          cy={progressSize.radius + progressSize.strokeWidth}
          r={progressSize.radius}
          fill="transparent"
          stroke={
            isCompleted ? "#10b981" : 
            isActive ? "#1e90ff" : 
            progressValue > 0 ? "#00bfff" : "#6b7280"
          }
          strokeWidth={progressSize.strokeWidth}
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          className={`transition-all duration-700 ease-out`}
          strokeLinecap="round"
        />
      </svg>
      
      {/* Icon centered inside the circle - FIXED: Better positioning and visibility */}
      <div className="absolute inset-0 flex items-center justify-center z-20">
        {React.cloneElement(icon, {
          className: `${progressSize.icon} ${
            isCompleted ? 'text-green-300' : 
            isActive ? 'text-white' : 
            'text-gray-300'
          } opacity-100 relative z-20 pointer-events-none`,
          fill: 'none',
          stroke: 'currentColor',
          strokeWidth: '2'
        })}
      </div>
    </div>
  );
});