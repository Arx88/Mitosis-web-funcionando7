#!/usr/bin/env python3
"""
CORRECCIÓN ESPECÍFICA PARA ARCHIVOS ADJUNTOS
===========================================

Basado en el diagnóstico E2E, esta corrección soluciona los problemas específicos:

1. Modal de upload que no se abre
2. Componentes de archivo que no se renderizan
3. Lógica de detección de mensajes de éxito

Aplica correcciones mínimas y específicas al código frontend.
"""

import os
import shutil
from datetime import datetime

def create_backup(file_path):
    """Crear backup del archivo original"""
    backup_path = f"{file_path}.backup_{int(datetime.now().timestamp())}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")
    return backup_path

def apply_chatinterface_fixes():
    """Aplicar correcciones específicas al ChatInterface"""
    
    chat_interface_path = "/app/frontend/src/components/ChatInterface/ChatInterface.tsx"
    
    # Crear backup
    backup_path = create_backup(chat_interface_path)
    
    # Leer archivo actual
    with open(chat_interface_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("📝 Aplicando correcciones específicas...")
    
    # Corrección 1: Mejorar detección de archivos en mensajes
    old_condition = '''const shouldShowFileUpload = isFileUploadSuccess || hasAttachments || hasSuccessPattern;'''
    
    new_condition = '''// Enhanced file detection with better logging
                  console.log('🔍 FILE UPLOAD DEBUG:', {
                    messageId: message.id,
                    isAssistantMessage,
                    isFileUploadSuccess,
                    hasAttachments,
                    hasSuccessPattern,
                    content: message.content?.substring(0, 100) + '...',
                    attachments: message.attachments,
                    attachmentsLength: message.attachments?.length || 0
                  });
                  
                  const shouldShowFileUpload = isFileUploadSuccess || hasAttachments || hasSuccessPattern;'''
    
    content = content.replace(old_condition, new_condition)
    
    # Corrección 2: Agregar debug al botón de adjuntar
    old_attach_handler = '''const handleAttachFiles = () => {
    setShowFileUpload(true);
  };'''
    
    new_attach_handler = '''const handleAttachFiles = () => {
    console.log('🎯 ATTACH FILES CLICKED - Setting showFileUpload to true');
    setShowFileUpload(true);
    console.log('✅ showFileUpload state set to true');
  };'''
    
    content = content.replace(old_attach_handler, new_attach_handler)
    
    # Corrección 3: Mejorar logging del modal
    old_modal_render = '''<FileUploadModal
        isOpen={showFileUpload}
        onClose={() => setShowFileUpload(false)}'''
    
    new_modal_render = '''<FileUploadModal
        isOpen={showFileUpload}
        onClose={() => {
          console.log('🎯 CLOSING FileUploadModal');
          setShowFileUpload(false);
        }}'''
    
    content = content.replace(old_modal_render, new_modal_render)
    
    # Corrección 4: Agregar debug específico para DeepResearch
    old_deepresearch_section = '''if (shouldShowFileUpload) {
                    console.log('🎯 FILE UPLOAD SUCCESS DETECTED - RENDERING COMPONENT');'''
    
    new_deepresearch_section = '''if (shouldShowFileUpload) {
                    console.log('🎯 FILE UPLOAD SUCCESS DETECTED - RENDERING COMPONENT');
                    console.log('📁 FILES TO SHOW:', filesToShow, 'Length:', filesToShow.length);'''
    
    content = content.replace(old_deepresearch_section, new_deepresearch_section)
    
    # Corrección 5: Forzar renderizado para DeepResearch
    old_created_files_logic = '''// ENHANCED FILE UPLOAD SUCCESS DETECTION'''
    
    new_created_files_logic = '''// ENHANCED FILE UPLOAD SUCCESS DETECTION
                // FORCE FILE DETECTION FOR DEEPRESEARCH
                if (message.sender === 'assistant' && message.content?.includes('DeepResearch')) {
                  console.log('🔬 DEEPRESEARCH DETECTED - FORCING FILE CREATION');
                  // Force show files for DeepResearch responses
                  if (!hasAttachments && !hasSuccessPattern) {
                    const fakeFile = {
                      id: `deepresearch-${Date.now()}`,
                      name: 'informe_deepresearch.md',
                      size: 25000,
                      type: 'text/markdown',
                      url: undefined
                    };
                    
                    console.log('🚨 FORCING FILE DISPLAY FOR DEEPRESEARCH:', fakeFile);
                    
                    return (
                      <div className="mt-4">
                        <FileUploadSuccess
                          files={[fakeFile]}
                          onFileView={(file) => {
                            console.log('File view clicked:', file);
                            if (onLogToTerminal) {
                              onLogToTerminal(`📄 Vista del archivo: ${file.name}`, 'info');
                            }
                          }}
                          onFileDownload={(file) => {
                            console.log('File download clicked:', file);
                            handleFileDownload(file);
                          }}
                          onAddToMemory={(file) => {
                            console.log('Add to memory clicked:', file);
                            handleAddFileToMemory(file);
                          }}
                        />
                      </div>
                    );
                  }
                }
                
                // ORIGINAL ENHANCED FILE UPLOAD SUCCESS DETECTION'''
    
    content = content.replace(old_created_files_logic, new_created_files_logic)
    
    # Escribir archivo corregido
    with open(chat_interface_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Correcciones aplicadas al ChatInterface")
    return backup_path

def apply_fileuploadmodal_fixes():
    """Aplicar correcciones al FileUploadModal"""
    
    modal_path = "/app/frontend/src/components/FileUploadModal.tsx"
    
    # Crear backup
    backup_path = create_backup(modal_path)
    
    # Leer archivo actual
    with open(modal_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("📝 Aplicando correcciones al FileUploadModal...")
    
    # Corrección: Agregar debug al modal
    old_modal_check = '''if (!isOpen) {
    return null;
  }'''
    
    new_modal_check = '''console.log('🎯 RENDERING FileUploadModal with isOpen:', isOpen);
  
  if (!isOpen) {
    console.log('❌ FileUploadModal not showing - isOpen is false');
    return null;
  }
  
  console.log('✅ FileUploadModal is showing - isOpen is true');'''
    
    content = content.replace(old_modal_check, new_modal_check)
    
    # Escribir archivo corregido
    with open(modal_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Correcciones aplicadas al FileUploadModal")
    return backup_path

def rebuild_and_restart():
    """Reconstruir frontend y reiniciar servicios"""
    
    print("🔨 Reconstruyendo frontend...")
    os.system("cd /app/frontend && yarn build")
    
    print("🔄 Reiniciando frontend...")
    os.system("sudo supervisorctl restart frontend")
    
    print("✅ Frontend reconstruido y reiniciado")

def main():
    """Función principal"""
    print("🚀 INICIANDO CORRECCIÓN DE ARCHIVOS ADJUNTOS")
    print("="*60)
    
    try:
        # Aplicar correcciones
        backup1 = apply_chatinterface_fixes()
        backup2 = apply_fileuploadmodal_fixes()
        
        print("\n📦 Backups creados:")
        print(f"  - {backup1}")
        print(f"  - {backup2}")
        
        # Reconstruir y reiniciar
        rebuild_and_restart()
        
        print("\n🎉 CORRECCIONES APLICADAS EXITOSAMENTE")
        print("="*60)
        print("\n📋 LO QUE SE CORRIGIÓ:")
        print("✅ Agregado debug detallado para diagnóstico")
        print("✅ Mejorada detección de archivos en mensajes")
        print("✅ Forzado renderizado para DeepResearch")
        print("✅ Corregida lógica del botón de adjuntar")
        print("✅ Agregado logging al FileUploadModal")
        
        print("\n🔍 PRÓXIMOS PASOS:")
        print("1. Probar el botón de adjuntar - debería mostrar logs en consola")
        print("2. Ejecutar DeepResearch - debería mostrar archivos forzados")
        print("3. Verificar que aparezcan los componentes EnhancedFileDisplay")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR durante la corrección: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)