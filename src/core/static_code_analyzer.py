import re
from pathlib import Path
from typing import List, Dict, Set

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
        
        # Arquivos de configuração e não-implementação para Node.js
        self.nodejs_config_files = {
            'package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
            'tsconfig.json', 'tsconfig.build.json', 'tsconfig.app.json',
            'jsconfig.json', 'webpack.config.js', 'webpack.config.ts',
            'vite.config.js', 'vite.config.ts', 'rollup.config.js',
            'babel.config.js', 'babel.config.json', '.babelrc', '.babelrc.js',
            'jest.config.js', 'jest.config.ts', 'vitest.config.js', 'vitest.config.ts',
            '.eslintrc', '.eslintrc.js', '.eslintrc.json', '.eslintrc.yml',
            'eslint.config.js', 'eslint.config.mjs', 'eslint.config.cjs',
            '.prettierrc', '.prettierrc.js', '.prettierrc.json', 'prettier.config.js',
            '.editorconfig', '.npmrc', '.yarnrc', '.nvmrc',
            'nodemon.json', 'next.config.js', 'next.config.mjs',
            'tailwind.config.js', 'tailwind.config.ts', 'postcss.config.js',
            'commitlint.config.js', 'lint-staged.config.js',
            '.huskyrc', '.lintstagedrc', '.stylelintrc'
        }
        
        # Padrões de nome de arquivo para ignorar
        self.nodejs_ignore_patterns = {
            r'.*\.config\.(js|ts|mjs|cjs|json)$',
            r'.*\.setup\.(js|ts)$',
            r'.*\.test\.(js|ts|jsx|tsx)$',
            r'.*\.spec\.(js|ts|jsx|tsx)$',
            r'.*\.d\.ts$',  # TypeScript declaration files
            r'.*\.stories\.(js|ts|jsx|tsx)$',  # Storybook
            r'.*\.mock\.(js|ts)$',
            r'.*\.fixture\.(js|ts)$',
            r'.*\.e2e\.(js|ts)$',
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
            feature_content = entry.get('feature_content', '')
            matched_content = entry.get('matched_content', '')

            author_repo = repository.replace("/", "_")
            normalized_repo_name = self._normalize_name(author_repo)
            repo_path = self.base_path / language / normalized_repo_name
            
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
            
            used_paths = self._analyze_test_file(test_file_path, language, repo_path)
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
                with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                records.append({
                    'name': name,
                    'path': str(path_obj),
                    'content': content
                })
            except Exception as e:
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
    
    def _is_nodejs_config_file(self, file_path: Path) -> bool:
        """Verifica se um arquivo é de configuração do Node.js"""
        filename = file_path.name
        
        # Verifica lista de arquivos de configuração conhecidos
        if filename in self.nodejs_config_files:
            return True
        
        # Verifica padrões regex
        for pattern in self.nodejs_ignore_patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return True
        
        return False
    
    def _is_nodejs_implementation_file(self, file_path: Path) -> bool:
        """Verifica se um arquivo é de implementação válida para Node.js"""
        # Extensões válidas de implementação
        valid_extensions = {'.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs'}
        
        if file_path.suffix not in valid_extensions:
            return False
        
        # Ignora arquivos de configuração
        if self._is_nodejs_config_file(file_path):
            return False
        
        # Verifica se está em diretórios de teste
        test_dirs = {'__tests__', '__mocks__', 'tests', 'test', 'specs', 'e2e'}
        if any(part in test_dirs for part in file_path.parts):
            return False
        
        return True
    
    def _resolve_nodejs_import(self, import_path: Path, repo_path: Path) -> List[str]:
        """
        Resolve um import de Node.js/TypeScript para arquivo(s) concreto(s).
        Retorna uma lista de caminhos de arquivos encontrados.
        """
        found_files = []
        extensions = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs']
        
        # 1. Tenta o caminho exato (arquivo completo com extensão)
        if import_path.exists() and import_path.is_file():
            if self._is_project_file(import_path, repo_path) and self._is_nodejs_implementation_file(import_path):
                found_files.append(str(import_path))
                return found_files
        
        # 2. Tenta adicionar extensões
        if not import_path.suffix:
            for ext in extensions:
                path_with_ext = import_path.with_suffix(ext)
                if path_with_ext.exists() and path_with_ext.is_file():
                    if self._is_project_file(path_with_ext, repo_path) and self._is_nodejs_implementation_file(path_with_ext):
                        found_files.append(str(path_with_ext))
                        return found_files
        
        # 3. Se o path é um diretório
        if import_path.exists() and import_path.is_dir():
            # Procura por index.* no diretório
            for ext in extensions:
                index_file = import_path / f'index{ext}'
                if index_file.exists() and index_file.is_file():
                    if self._is_project_file(index_file, repo_path) and self._is_nodejs_implementation_file(index_file):
                        found_files.append(str(index_file))
            
            # Se não encontrou index, retorna arquivos relevantes do diretório
            if not found_files:
                for ext in extensions:
                    for file in import_path.glob(f'*{ext}'):
                        if file.is_file() and self._is_project_file(file, repo_path) and self._is_nodejs_implementation_file(file):
                            found_files.append(str(file))
        
        # 4. Tenta como diretório (mesmo se não existir ainda)
        if not found_files:
            for ext in extensions:
                index_file = import_path / f'index{ext}'
                if index_file.exists() and index_file.is_file():
                    if self._is_project_file(index_file, repo_path) and self._is_nodejs_implementation_file(index_file):
                        found_files.append(str(index_file))
        
        return found_files
    
    def _analyze_nodejs(self, test_file_path: Path, repo_path: Path) -> List[str]:
        """Analisa arquivo Node.js/TypeScript com heurística melhorada"""
        used_files = set()
        
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Padrões para capturar imports/requires
            require_pattern = r'require\s*\(\s*["\']([^"\']+)["\']\s*\)'
            import_pattern = r'import\s+(?:(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)\s+from\s+)?["\']([^"\']+)["\']'
            dynamic_import_pattern = r'import\s*\(\s*["\']([^"\']+)["\']\s*\)'
            
            requires = re.findall(require_pattern, content)
            imports = re.findall(import_pattern, content)
            dynamic_imports = re.findall(dynamic_import_pattern, content)
            
            all_imports = requires + imports + dynamic_imports
            base_dir = test_file_path.parent
            
            for import_path in all_imports:
                # Ignora imports de módulos externos
                if not import_path.startswith('.') and not import_path.startswith('/'):
                    # Verifica aliases de path
                    if import_path.startswith('@/') or import_path.startswith('~/'):
                        clean_path = import_path.lstrip('@/').lstrip('~/')
                        potential_path = repo_path / clean_path
                    else:
                        continue
                else:
                    try:
                        potential_path = (base_dir / import_path).resolve()
                        potential_path.relative_to(repo_path)
                    except (ValueError, OSError):
                        continue
                
                found_files = self._resolve_nodejs_import(potential_path, repo_path)
                used_files.update(found_files)
                
        except Exception as e:
            print(f"Erro ao analisar arquivo Node.js {test_file_path}: {e}")
        
        return sorted(list(used_files))
    
    def _analyze_java(self, test_file_path: Path, repo_path: Path) -> List[str]:
        """Analisa arquivo Java"""
        used_files = set()
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            import_pattern = r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*);'
            imports = re.findall(import_pattern, content)
            new_pattern = r'new\s+([A-Z][a-zA-Z0-9_]*)\s*\('
            new_classes = re.findall(new_pattern, content)
            static_pattern = r'([A-Z][a-zA-Z0-9_]*)\.[a-zA-Z_][a-zA-Z0-9_]*\s*\('
            static_classes = re.findall(static_pattern, content)
            
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
                'third_party', 'external', '.git', 'coverage',
                '.next', '.nuxt', 'out', '.cache'
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