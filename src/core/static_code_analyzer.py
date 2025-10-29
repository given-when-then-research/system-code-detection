import re
from pathlib import Path
from typing import List, Dict

class StaticCodeAnalyzer:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.language_analyzers = {
            'java': self._analyze_java,
            'cpp': self._analyze_cpp,
            'go': self._analyze_go,
            'kotlin': self._analyze_kotlin,
            'lua': self._analyze_lua,
            'nodejs': self._analyze_nodejs,
            'ocaml': self._analyze_ocaml,
            'ruby': self._analyze_ruby,
            'scala': self._analyze_scala
        }
    
    def _normalize_name(self, name: str) -> str:
        """Normaliza nome removendo caracteres especiais"""
        return re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower())
    
    def analyze_dataset(self, dataset: List[Dict]) -> Dict:
        """Analisa todo o dataset e retorna os arquivos utilizados para cada entrada"""
        results = []
        
        for entry in dataset:
            repository = entry['repository']
            language = entry['language']
            feature_file = entry['feature_file']
            test_file = entry['used_in'][0]['file']
            # novos campos solicitados
            feature_content = entry.get('feature_content', '')
            matched_content = entry.get('matched_content', '')

            # Normaliza o nome do repositório
            author_repo = repository.replace("/", "_")  # "autor_repo"
            normalized_repo_name = self._normalize_name(author_repo)
            
            # Caminho completo do repositório
            repo_path = self.base_path / language / normalized_repo_name
            
            # Caso o repo não exista
            if not repo_path.exists():
                print(f"Repositório não encontrado: {repo_path}")
                result = {
                    'repository': repository,
                    'language': language,
                    'normalized_repo_path': str(repo_path),
                    'feature_file': feature_file,
                    'test_file': str(repo_path / test_file),
                    'feature_content': feature_content,
                    'matched_content': matched_content,
                    'system_code_files': []
                }
                results.append(result)
                continue
            
            # Caminho completo do arquivo de teste
            test_file_path = repo_path / test_file
            
            if not test_file_path.exists():
                print(f"Arquivo de teste não encontrado: {test_file_path}")
                result = {
                    'repository': repository,
                    'language': language,
                    'normalized_repo_path': str(repo_path),
                    'feature_file': feature_file,
                    'test_file': str(test_file_path),
                    'feature_content': feature_content,
                    'matched_content': matched_content,
                    'system_code_files': []
                }
                results.append(result)
                continue
            
            # Analisa o arquivo de teste -> retorna caminhos de arquivos usados
            used_paths = self._analyze_test_file(test_file_path, language, repo_path)

            # Converte paths em {name, path, content}
            used_files_records = self._build_file_records(used_paths)

            result = {
                'repository': repository,
                'language': language,
                'normalized_repo_path': str(repo_path),
                'feature_file': feature_file,
                'feature_content': feature_content,
                'step_definitions_file': str(test_file),
                'step_definitions_content': matched_content,
                'system_code_files': used_files_records
            }
            
            results.append(result)
        
        return results
    
    def _build_file_records(self, paths: List[str]) -> List[Dict]:
        """Dado uma lista de caminhos, retorna objetos com name, path e content."""
        records = []
        for p in sorted(set(paths)):
            try:
                path_obj = Path(p)
                name = path_obj.name
                # Leitura robusta – ignora erros de decoding
                with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                records.append({
                    'name': name,
                    'path': str(path_obj),
                    'content': content
                })
            except Exception as e:
                # Se falhar leitura, ainda retornamos name e path
                records.append({
                    'name': Path(p).name,
                    'path': p,
                    'content': f'__READ_ERROR__: {e}'
                })
        return records

    def _analyze_test_file(self, test_file_path: Path, language: str, repo_path: Path) -> List[str]:
        """Analisa um arquivo de teste específico e retorna caminhos de arquivos usados."""
        if language in self.language_analyzers:
            return self.language_analyzers[language](test_file_path, repo_path)
        else:
            print(f"Linguagem não suportada: {language}")
            return []
    
    def _analyze_java(self, test_file_path: Path, repo_path: Path) -> List[str]:
        """Analisa arquivo Java"""
        used_files = set()
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extrai imports
            import_pattern = r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*);'
            imports = re.findall(import_pattern, content)
            
            # Extrai classes instanciadas (new ClassName())
            new_pattern = r'new\s+([A-Z][a-zA-Z0-9_]*)\s*\('
            new_classes = re.findall(new_pattern, content)
            
            # Extrai chamadas de métodos estáticos (ClassName.method())
            static_pattern = r'([A-Z][a-zA-Z0-9_]*)\.[a-zA-Z_][a-zA-Z0-9_]*\s*\('
            static_classes = re.findall(static_pattern, content)
            
            # Procura pelos arquivos correspondentes no projeto
            all_references = set(imports + new_classes + static_classes)
            for ref in all_references:
                class_name = ref.split('.')[-1]
                java_files = list(repo_path.rglob(f"{class_name}.java"))
                for java_file in java_files:
                    if self._is_project_file(java_file, repo_path):
                        used_files.add(str(java_file))
        except Exception as e:
            print(f"Erro ao analisar arquivo Java {test_file_path}: {e}")
        return sorted(list(used_files))
    
    def _analyze_cpp(self, test_file_path: Path, repo_path: Path) -> List[str]:
        """Analisa arquivo C++"""
        used_files = set()
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            include_pattern = r'#include\s*"([^"]+)"'
            includes = re.findall(include_pattern, content)
            for include in includes:
                header_path = repo_path / include
                if header_path.exists() and self._is_project_file(header_path, repo_path):
                    used_files.add(str(header_path))
                cpp_path = header_path.with_suffix('.cpp')
                if cpp_path.exists() and self._is_project_file(cpp_path, repo_path):
                    used_files.add(str(cpp_path))
        except Exception as e:
            print(f"Erro ao analisar arquivo C++ {test_file_path}: {e}")
        return sorted(list(used_files))
    
    def _analyze_go(self, test_file_path: Path, repo_path: Path) -> List[str]:
        """Analisa arquivo Go"""
        used_files = set()
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # Heurística: qualquer .go do projeto que contenha identificadores do teste
            for go_file in repo_path.rglob("*.go"):
                if self._is_project_file(go_file, repo_path):
                    if self._file_contains_references(go_file, content):
                        used_files.add(str(go_file))
        except Exception as e:
            print(f"Erro ao analisar arquivo Go {test_file_path}: {e}")
        return sorted(list(used_files))
    
    def _analyze_kotlin(self, test_file_path: Path, repo_path: Path) -> List[str]:
        """Analisa arquivo Kotlin"""
        used_files = set()
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            import_pattern = r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)'
            imports = re.findall(import_pattern, content)
            new_pattern = r'([A-Z][a-zA-Z0-9_]*)\s*\('
            classes = re.findall(new_pattern, content)
            all_references = set(imports + classes)
            for ref in all_references:
                class_name = ref.split('.')[-1]
                kt_files = list(repo_path.rglob(f"{class_name}.kt"))
                for kt_file in kt_files:
                    if self._is_project_file(kt_file, repo_path):
                        used_files.add(str(kt_file))
        except Exception as e:
            print(f"Erro ao analisar arquivo Kotlin {test_file_path}: {e}")
        return sorted(list(used_files))
    
    def _analyze_lua(self, test_file_path: Path, repo_path: Path) -> List[str]:
        """Analisa arquivo Lua"""
        used_files = set()
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            require_pattern = r'require\s*\(\s*["\']([^"\']+)["\']\s*\)'
            requires = re.findall(require_pattern, content)
            load_pattern = r'(?:dofile|loadfile)\s*\(\s*["\']([^"\']+)["\']\s*\)'
            loads = re.findall(load_pattern, content)
            for req in requires + loads:
                lua_path = repo_path / f"{req}.lua"
                if lua_path.exists() and self._is_project_file(lua_path, repo_path):
                    used_files.add(str(lua_path))
        except Exception as e:
            print(f"Erro ao analisar arquivo Lua {test_file_path}: {e}")
        return sorted(list(used_files))
    
    def _analyze_nodejs(self, test_file_path: Path, repo_path: Path) -> List[str]:
        """Analisa arquivo Node.js/TypeScript"""
        used_files = set()
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            require_pattern = r'require\s*\(\s*["\']([^"\']+)["\']\s*\)'
            import_pattern = r'import\s+.*from\s+["\']([^"\']+)["\']'
            requires = re.findall(require_pattern, content)
            imports = re.findall(import_pattern, content)
            for req in requires + imports:
                # Se o caminho for relativo (começa com .), resolve a partir do diretório do arquivo de teste
                if req.startswith('.'):
                    # Remove a extensão do arquivo de teste para obter o diretório
                    base_dir = test_file_path.parent
                    # Tenta resolver o caminho
                    potential_path = base_dir / req
                # Se o caminho for absoluto ou de módulo (não começa com .), a lógica de busca é mais complexa.
                # Para simplificar, vamos assumir que se não for relativo, é um módulo e ignorar por enquanto,
                # ou tentar encontrar o arquivo diretamente no repo_path se for um caminho absoluto.
                # Como o exemplo do usuário é relativo, vamos focar nisso.
                else:
                    # Para imports não relativos, vamos tentar buscar no repo_path, assumindo que
                    # são caminhos absolutos dentro do projeto (ex: @/components/X) ou módulos (que serão ignorados).
                    # A heurística de busca é complexa, mas para caminhos absolutos do projeto,
                    # podemos tentar resolver a partir da raiz do repositório.
                    potential_path = repo_path / req
                    # Para imports de módulos (ex: 'react'), a heurística atual não vai funcionar bem,
                    # mas o objetivo é encontrar arquivos do projeto. Vamos focar em arquivos com extensão.
                    
                # Lista de extensões comuns em Node.js/TS
                extensions = ['.js', '.jsx', '.ts', '.tsx', '.json']

                # 1. Tenta o caminho exato
                if potential_path.exists() and self._is_project_file(potential_path, repo_path):
                    used_files.add(str(potential_path))
                    continue

                # 2. Tenta adicionar extensões
                for ext in extensions:
                    path_with_ext = potential_path.with_suffix(ext)
                    if path_with_ext.exists() and self._is_project_file(path_with_ext, repo_path):
                        used_files.add(str(path_with_ext))
                        break # Encontrou, passa para o próximo require/import

                # 3. Tenta como diretório (index.js/index.ts)
                path_as_dir = potential_path / 'index'
                for ext in extensions:
                    path_with_index_ext = path_as_dir.with_suffix(ext)
                    if path_with_index_ext.exists() and self._is_project_file(path_with_index_ext, repo_path):
                        used_files.add(str(path_with_index_ext))
                        break # Encontrou, passa para o próximo require/import
        except Exception as e:
            print(f"Erro ao analisar arquivo Node.js {test_file_path}: {e}")
        return sorted(list(used_files))
    
    def _analyze_ocaml(self, test_file_path: Path, repo_path: Path) -> List[str]:
        """Analisa arquivo OCaml"""
        used_files = set()
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            open_pattern = r'open\s+([A-Z][a-zA-Z0-9_]*)'
            opens = re.findall(open_pattern, content)
            module_pattern = r'([A-Z][a-zA-Z0-9_]*)\.[a-zA-Z_][a-zA-Z0-9_]*'
            modules = re.findall(module_pattern, content)
            all_modules = set(opens + modules)
            for module in all_modules:
                ml_path = repo_path / f"{module.lower()}.ml"
                if ml_path.exists() and self._is_project_file(ml_path, repo_path):
                    used_files.add(str(ml_path))
                mli_path = repo_path / f"{module.lower()}.mli"
                if mli_path.exists() and self._is_project_file(mli_path, repo_path):
                    used_files.add(str(mli_path))
        except Exception as e:
            print(f"Erro ao analisar arquivo OCaml {test_file_path}: {e}")
        return sorted(list(used_files))
    
    def _analyze_ruby(self, test_file_path: Path, repo_path: Path) -> List[str]:
        """Analisa arquivo Ruby"""
        used_files = set()
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            require_pattern = r'require_relative\s+["\']([^"\']+)["\']'
            require_relative = re.findall(require_pattern, content)
            require_abs_pattern = r'require\s+["\']([^"\']+)["\']'
            requires = re.findall(require_abs_pattern, content)
            for req in require_relative:
                rb_path = repo_path / f"{req}.rb"
                if rb_path.exists() and self._is_project_file(rb_path, repo_path):
                    used_files.add(str(rb_path))
            for req in requires:
                if not req.startswith('.'):
                    rb_files = list(repo_path.rglob(f"{req}.rb"))
                    for rb_file in rb_files:
                        if self._is_project_file(rb_file, repo_path):
                            used_files.add(str(rb_file))
        except Exception as e:
            print(f"Erro ao analisar arquivo Ruby {test_file_path}: {e}")
        return sorted(list(used_files))
    
    def _analyze_scala(self, test_file_path: Path, repo_path: Path) -> List[str]:
        """Analisa arquivo Scala"""
        used_files = set()
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            import_pattern = r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)'
            imports = re.findall(import_pattern, content)
            class_pattern = r'new\s+([A-Z][a-zA-Z0-9_]*)'
            object_pattern = r'([A-Z][a-zA-Z0-9_]*)\.[a-zA-Z_][a-zA-Z0-9_]*'
            classes = re.findall(class_pattern, content)
            objects = re.findall(object_pattern, content)
            all_references = set(imports + classes + objects)
            for ref in all_references:
                class_name = ref.split('.')[-1]
                scala_files = list(repo_path.rglob(f"{class_name}.scala"))
                for scala_file in scala_files:
                    if self._is_project_file(scala_file, repo_path):
                        used_files.add(str(scala_file))
        except Exception as e:
            print(f"Erro ao analisar arquivo Scala {test_file_path}: {e}")
        return sorted(list(used_files))
    
    def _is_project_file(self, file_path: Path, repo_path: Path) -> bool:
        """Verifica se um arquivo é do projeto (não de biblioteca externa)"""
        try:
            file_path.relative_to(repo_path)
            exclude_dirs = {
                'node_modules', 'vendor', 'target', 'build', 'dist',
                '.gradle', '.maven', 'lib', 'libs', 'dependencies',
                'third_party', 'external', '.git'
            }
            for part in file_path.parts:
                if part in exclude_dirs:
                    return False
            return True
        except ValueError:
            return False
    
    def _file_contains_references(self, file_path: Path, test_content: str) -> bool:
        """Verifica se um arquivo contém funções/tipos referenciados no teste"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_content = f.read()
            identifiers = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', test_content)
            for identifier in set(identifiers):
                if len(identifier) > 3 and identifier in file_content:
                    return True
            return False
        except Exception:
            return False