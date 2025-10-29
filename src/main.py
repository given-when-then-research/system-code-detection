import json
from pathlib import Path

from core.static_code_analyzer import StaticCodeAnalyzer

def main():
    BASE_PATH = Path("/home/luciano/Documentos/Github/llm-bdd-research/repositories")

    dataset_path = '../dataset/consolidated_dataset.json'
    
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar dataset: {e}")
        return
    
    analyzer = StaticCodeAnalyzer(str(BASE_PATH))
    
    print("Iniciando análise do dataset...")
    results = analyzer.analyze_dataset(dataset)
    
    # Salva os resultados
    output_path = "./output/GivenWhenThen_dataset.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Análise concluída! Resultados salvos em: {output_path}")
    
    # Estatísticas (mantidas)
    analysis_results = results
    total_entries = len(analysis_results)
    entries_with_zero_files = len([entry for entry in analysis_results if len(entry['bla_project_files']) == 0])
    entries_with_files = total_entries - entries_with_zero_files
    total_files_found = sum(len(entry['bla_project_files']) for entry in analysis_results)
    
    language_stats = {}
    for entry in analysis_results:
        lang = entry['language']
        if lang not in language_stats:
            language_stats[lang] = {'total': 0, 'with_files': 0, 'zero_files': 0, 'files_count': 0}
        language_stats[lang]['total'] += 1
        language_stats[lang]['files_count'] += len(entry['bla_project_files'])
        if len(entry['bla_project_files']) == 0:
            language_stats[lang]['zero_files'] += 1
        else:
            language_stats[lang]['with_files'] += 1
    
    print(f"\n{'='*60}")
    print(f"ESTATÍSTICAS GERAIS")
    print(f"{'='*60}")
    print(f"Total de entradas analisadas: {total_entries}")
    print(f"Entradas com arquivos encontrados: {entries_with_files} ({entries_with_files/total_entries*100:.1f}%)")
    print(f"Entradas com ZERO arquivos encontrados: {entries_with_zero_files} ({entries_with_zero_files/total_entries*100:.1f}%)")
    print(f"Total de arquivos de projeto encontrados: {total_files_found}")
    
    if entries_with_files > 0:
        print(f"Média de arquivos por entrada (excluindo zeros): {total_files_found/entries_with_files:.2f}")
    
    print(f"\n{'='*60}")
    print(f"ESTATÍSTICAS POR LINGUAGEM")
    print(f"{'='*60}")
    print(f"{'Linguagem':<12} {'Total':<8} {'Com Arqs':<10} {'Zero Arqs':<10} {'% Zero':<8} {'Tot Arqs':<10}")
    print(f"{'-'*60}")
    
    for lang in sorted(language_stats.keys()):
        stats = language_stats[lang]
        zero_percentage = (stats['zero_files'] / stats['total']) * 100
        print(f"{lang:<12} {stats['total']:<8} {stats['with_files']:<10} {stats['zero_files']:<10} {zero_percentage:<7.1f}% {stats['files_count']:<10}")


if __name__ == "__main__":
    main()