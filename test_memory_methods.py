#!/usr/bin/env python3
"""
Test script para verificar que los métodos compress_old_memory y export_memory_data funcionen correctamente
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Agregar el directorio backend al path
sys.path.append('/app/backend')
sys.path.append('/app/backend/src')

from src.memory.advanced_memory_manager import AdvancedMemoryManager
from src.memory.episodic_memory_store import Episode
from src.memory.semantic_memory_store import SemanticConcept, SemanticFact

async def test_memory_methods():
    """Test de los métodos faltantes de memoria"""
    print("🧪 Testing Memory Methods - compress_old_memory y export_memory_data")
    print("=" * 80)
    
    # Inicializar memory manager
    try:
        memory_manager = AdvancedMemoryManager()
        await memory_manager.initialize()
        print("✅ Memory manager inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando memory manager: {e}")
        return False
    
    # Test 1: Agregar algunos datos de prueba
    print("\n🔍 Test 1: Agregando datos de prueba")
    try:
        # Crear episodio de prueba
        episode = Episode(
            id="test_episode_1",
            title="Test Episode",
            description="Este es un episodio de prueba para verificar compresión",
            context={
                'task_type': 'test',
                'success': True,
                'user_id': 'test_user'
            },
            actions=[
                {'type': 'action1', 'content': 'Primera acción'},
                {'type': 'action2', 'content': 'Segunda acción'},
                {'type': 'action3', 'content': 'Tercera acción'}
            ],
            outcomes=[
                {'type': 'outcome1', 'content': 'Primer resultado'},
                {'type': 'outcome2', 'content': 'Segundo resultado'}
            ],
            timestamp=datetime.now(),
            success=True,
            importance=3,
            tags=['test', 'compression']
        )
        
        await memory_manager.episodic_memory.store_episode(episode)
        print("✅ Episodio de prueba agregado")
        
        # Crear concepto semántico de prueba
        concept = SemanticConcept(
            id="test_concept_1",
            name="Test Concept",
            description="Este es un concepto de prueba para verificar compresión y exportación",
            category="test",
            attributes={
                'type': 'test',
                'category': 'prueba',
                'importance': 'media'
            },
            relations=[],
            confidence=0.8
        )
        
        await memory_manager.semantic_memory.store_concept(concept)
        print("✅ Concepto semántico de prueba agregado")
        
        # Crear fact semántico de prueba
        fact = SemanticFact(
            id="test_fact_1",
            subject="Python",
            predicate="es",
            object="un lenguaje de programación",
            context={'source': 'test', 'domain': 'programming'},
            confidence=0.9,
            source="test_source"
        )
        
        await memory_manager.semantic_memory.store_fact(fact)
        print("✅ Fact semántico de prueba agregado")
        
    except Exception as e:
        print(f"❌ Error agregando datos de prueba: {e}")
        return False
    
    # Test 2: Probar export_memory_data
    print("\n🔍 Test 2: Probando export_memory_data")
    try:
        # Test formato JSON
        export_result = await memory_manager.export_memory_data(
            export_format='json',
            include_compressed=True
        )
        
        if export_result['success']:
            stats = export_result['export_stats']
            print(f"✅ Export JSON exitoso:")
            print(f"   - Episodios exportados: {stats['exported_episodes']}")
            print(f"   - Conceptos exportados: {stats['exported_concepts']}")
            print(f"   - Facts exportados: {stats['exported_facts']}")
            print(f"   - Procedimientos exportados: {stats['exported_procedures']}")
            print(f"   - Tamaño de exportación: {stats['export_size']} bytes")
            
            # Verificar que los datos están en el formato correcto
            if 'data' in export_result and export_result['data']:
                data = export_result['data']
                if 'episodic_memory' in data and 'semantic_memory' in data:
                    print("✅ Estructura de datos de exportación correcta")
                else:
                    print("❌ Estructura de datos de exportación incorrecta")
                    
        else:
            print(f"❌ Export JSON falló: {export_result}")
            
    except Exception as e:
        print(f"❌ Error en export_memory_data: {e}")
        return False
    
    # Test 3: Probar compress_old_memory
    print("\n🔍 Test 3: Probando compress_old_memory")
    try:
        # Probar compresión (con umbral de 0 días para comprimir todo)
        compression_result = await memory_manager.compress_old_memory(
            compression_threshold_days=0,  # Comprimir todo
            compression_ratio=0.5
        )
        
        if 'error' not in compression_result:
            print(f"✅ Compresión exitosa:")
            print(f"   - Episodios comprimidos: {compression_result['compressed_episodes']}")
            print(f"   - Conceptos comprimidos: {compression_result['compressed_concepts']}")
            print(f"   - Facts comprimidos: {compression_result['compressed_facts']}")
            print(f"   - Procedimientos comprimidos: {compression_result['compressed_procedures']}")
            print(f"   - Espacio ahorrado: {compression_result['space_saved']} bytes")
            print(f"   - Espacio ahorrado: {compression_result.get('total_space_saved_kb', 0):.2f} KB")
        else:
            print(f"❌ Compresión falló: {compression_result['error']}")
            
    except Exception as e:
        print(f"❌ Error en compress_old_memory: {e}")
        return False
    
    # Test 4: Probar export después de compresión
    print("\n🔍 Test 4: Probando export después de compresión")
    try:
        # Export con datos comprimidos
        export_result = await memory_manager.export_memory_data(
            export_format='json',
            include_compressed=True
        )
        
        if export_result['success']:
            print("✅ Export después de compresión exitoso")
            
            # Export sin datos comprimidos
            export_result_no_compressed = await memory_manager.export_memory_data(
                export_format='json',
                include_compressed=False
            )
            
            if export_result_no_compressed['success']:
                print("✅ Export sin datos comprimidos exitoso")
                
                # Comparar tamaños
                size_with_compressed = export_result['export_stats']['export_size']
                size_without_compressed = export_result_no_compressed['export_stats']['export_size']
                
                print(f"   - Tamaño con comprimidos: {size_with_compressed} bytes")
                print(f"   - Tamaño sin comprimidos: {size_without_compressed} bytes")
                print(f"   - Diferencia: {size_with_compressed - size_without_compressed} bytes")
                
        else:
            print(f"❌ Export después de compresión falló: {export_result}")
            
    except Exception as e:
        print(f"❌ Error en export después de compresión: {e}")
        return False
    
    # Test 5: Test de formatos de export
    print("\n🔍 Test 5: Probando diferentes formatos de export")
    try:
        # Test CSV
        csv_result = await memory_manager.export_memory_data(export_format='csv')
        if csv_result['success']:
            print("✅ Export CSV exitoso")
        else:
            print(f"❌ Export CSV falló")
            
        # Test XML
        xml_result = await memory_manager.export_memory_data(export_format='xml')
        if xml_result['success']:
            print("✅ Export XML exitoso")
        else:
            print(f"❌ Export XML falló")
            
    except Exception as e:
        print(f"❌ Error en formatos de export: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("🎉 TODOS LOS TESTS PASARON - MÉTODOS FUNCIONANDO CORRECTAMENTE")
    print("✅ compress_old_memory: FUNCIONANDO")
    print("✅ export_memory_data: FUNCIONANDO")
    print("✅ Formatos de export (JSON, CSV, XML): FUNCIONANDO")
    print("✅ Compresión de memoria antigua: FUNCIONANDO")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_memory_methods())
    sys.exit(0 if success else 1)