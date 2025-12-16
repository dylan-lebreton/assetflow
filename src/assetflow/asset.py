import inspect
import warnings
from typing import Optional, Sequence, Union, Mapping, Dict, Any, Callable

from typeguard import typechecked
from typing_extensions import get_origin, get_args

from .combiner import Combiner
from .dependency import Dependency
from .dumper import Dumper
from .dumper_factory import DumperFactory
from .exceptions import AssetDefinitionError
from .executor import Executor
from .executors import SequentialExecutor
from .loader import Loader
from .loader_factory import LoaderFactory
from .logic import Logic, FunctionLogic


class Asset:

    @typechecked
    def __init__(
            self,
            *,
            logic: Optional[Logic] = None,
            dumper: Optional[Union[Dumper, Sequence[Dumper], DumperFactory]] = None,
            loader: Optional[Union[Loader, Sequence[Loader], LoaderFactory]] = None,
            dependencies: Optional[Mapping[str, "Asset"]] = None,
            combiner: Optional[Combiner] = None,
            executor: Optional[Executor] = None,
            **extra: Any
    ) -> None:

        self.logic = logic
        self.dumper = dumper
        self.loader = loader
        self.dependencies = dependencies
        self.combiner = combiner
        self.executor = executor
        self.children = []
        self.__extra = extra

        self.__configure()

    def __configure(self):

        # Useless asset
        if (self.logic is None) and (self.dumper is None) and (self.loader is None):
            raise AssetDefinitionError(
                error="`logic`, `dumper` and `loader` are all None.",
                explanation="Asset is useless.",
                fix="Provide `loader` argument, `logic` and `dumper` arguments, or both.",
            )

        # Global invariants
        if self.dumper is not None and self.logic is None:
            raise AssetDefinitionError(
                error="`dumper` provided but `logic` is None.",
                explanation="If `logic` is None, `dumper` has no logic result to dump.",
                fix="Remove `dumper` argument or provide a `logic` argument.",
            )
        if self.logic is not None and self.dumper is None:
            raise AssetDefinitionError(
                error="`logic` provided but `dumper` is None.",
                explanation="If `dumper` is None, `logic` result cannot be dumped.",
                fix="Remove `logic` argument, or provide a `dumper` argument, or use a function instead of an asset.",
            )

        # Source asset
        if self.logic is None and self.dumper is None and self.loader is not None:
            self.__configure_source_asset()

        # Terminal asset
        if self.logic is not None and self.dumper is not None and self.loader is None:
            self.__configure_terminal_asset()

        # Intermediate asset
        if self.logic is not None and self.dumper is not None and self.loader is not None:
            self.__configure_intermediate_asset()

    def __configure_source_asset(self):
        if self.dependencies:
            raise AssetDefinitionError(
                error="`dependencies` provided but `logic` is None.",
                explanation="If `logic` is None, no `dependencies` can be injected in the logic function.",
                fix="Remove `dependencies` argument or provide `logic` and `dumper` arguments."
            )

        if self.combiner is not None:
            raise AssetDefinitionError(
                error="`combiner` provided but `logic` is None.",
                explanation="If `logic` is None, there are no `dependencies` to combine.",
                fix="Remove `combiner` argument or provide `logic` and `dumper` arguments.",
            )

        if self.executor is not None:
            raise AssetDefinitionError(
                error="`executor` provided but `logic` is None.",
                explanation="If `logic` is None, there is nothing to execute.",
                fix="Remove `executor` argument or provide `logic` and `dumper` arguments.",
            )

        if isinstance(self.loader, LoaderFactory):
            raise AssetDefinitionError(
                error="`loader` is of type `LoaderFactory` but `logic` is None.",
                explanation="Loader factories are reserved for dynamically generating loaders "
                            "for assets with `logic` and `dependencies`.",
                fix="Provide a different `loader` type (`Loader`, Sequence[Loader]).",
            )
        # Parameters are already well-defined
        elif isinstance(self.loader, Loader):
            ...
        # If several loaders, one child by loader
        else:
            self.children = [
                self.__class__(loader=l, **self.__extra) for l in self.loader
            ]

    def __configure_terminal_asset(self):
        if isinstance(self.dumper, Dumper):
            self.__configure_atomic_terminal_asset()
        else:
            self.__configure_composite_terminal_asset()

    def __configure_atomic_terminal_asset(self):
        # dumper = Dumper => no children => no need of combiner as every dependency must be gathered
        if self.combiner is not None:
            raise AssetDefinitionError(
                error="`combiner` provided with `dumper` of type `Dumper`.",
                explanation="`dumper` of type `Dumper` forces each dependency to be gathered, "
                            "`combiner` is not allowed.",
                fix="Remove `combiner` argument or provide a different `dumper` type "
                    "(`DumperFactory`, Sequence[Dumper]).",
            )

        # Warning if executor provided
        if self.executor is not None:
            raise AssetDefinitionError(
                error="`executor` provided with `dumper` of type `Dumper`.",
                explanation="`dumper` of type `Dumper` forces logic to be computed once by gathering the dependencies. "
                            "Executor is useless.",
                fix="Remove `executor` argument or provide a different `dumper` type "
                    "(`DumperFactory`, Sequence[Dumper])."
            )
        # Warning if no dependencies
        if not self.dependencies:
            warnings.warn(
                "No `dependencies` provided while the asset has a computation logic. "
                "Please verify that the `logic` is not acting as a loader, and that any external inputs "
                "that could be modeled as assets are properly defined as assets with loaders.",
                UserWarning,
                stacklevel=2,
            )

        # Nothing else to do, the asset is well-defined

    def __configure_composite_terminal_asset(self):
        if isinstance(self.dumper, DumperFactory):
            if not self.dependencies:
                raise AssetDefinitionError(
                    error="`dumper` is of type `DumperFactory` but no `dependencies` provided.",
                    explanation=(
                        "Dumper factories are reserved for dynamically generating dumpers based on "
                        "combinations of dependency results."
                    ),
                    fix=(
                        "Provide `dependencies` argument or provide a `dumper` of type `Dumper`."
                    ),
                )
            if self.combiner is None:
                raise AssetDefinitionError(
                    error="`dumper` is of type `DumperFactory` but no `combiner` provided.",
                    explanation="The default combiner gathers the dependencies, prohibiting multiple dumpers.",
                    fix="Provide `combiner` argument or provide a `dumper` of type `Dumper`."
                )

            logic_inputs_combinations = self.combiner.combine(**self.dependencies)
            for logic_inputs in logic_inputs_combinations:
                self.children.append(
                    self.__class__(
                        logic=self.logic,
                        dumper=self.dumper.build(**logic_inputs),
                        dependencies=logic_inputs,
                        **self.__extra
                    )
                )

        else:
            if not self.dependencies:
                raise AssetDefinitionError(
                    error="`dumper` is of type Sequence[Dumper] but no `dependencies` provided.",
                    explanation="Without dependencies, the logic returns the same result, prohibiting multiple dumpers.",
                    fix="Provide `dependencies` argument or provide a `dumper` of type `Dumper`."
                )
            if self.combiner is None:
                raise AssetDefinitionError(
                    error="`dumper` is of type Sequence[Dumper] but no `combiner` provided.",
                    explanation="The default combiner gathers the dependencies, prohibiting multiple dumpers.",
                    fix="Provide `combiner` argument or provide a `dumper` of type `Dumper`."
                )

            logic_inputs_combinations = list(self.combiner.combine(**self.dependencies))
            n_combinations = len(logic_inputs_combinations)
            n_dumpers = len(self.dumper)
            if n_combinations != n_dumpers:
                raise AssetDefinitionError(
                    error=f"Mismatching number of dumpers.",
                    explanation=f"`combiner` generates {n_combinations} inputs on which to apply the logic, "
                                f"but `dumper` provides {n_dumpers} dumpers to persist the results.",
                    fix=f"Provide `dumper` of type Sequence[Dumper] with matching number of dumpers ({n_combinations}), "
                        "or provide `dumper` of type `DumperFactory` to dynamically generate the dumpers."
                )
            for i, logic_inputs in enumerate(logic_inputs_combinations):
                self.children.append(
                    self.__class__(
                        logic=self.logic,
                        dumper=self.dumper[i],
                        dependencies=logic_inputs,
                        **self.__extra
                    )
                )

    def __configure_intermediate_asset(self):
        if isinstance(self.dumper, Dumper):
            if isinstance(self.loader, Loader):
                self.__configure_atomic_intermediate_asset()
            else:
                loader_type_name = type(self.loader).__name__

                if isinstance(self.loader, LoaderFactory):
                    loader_type_name = f"`{loader_type_name}`"

                raise AssetDefinitionError(
                    error=f"`dumper` is of type `Dumper` but `loader` is of type {loader_type_name}.",
                    explanation=f"`dumper` of type `Dumper` implies dumping a single element, "
                                "which forces `loader` to load only one element, and therefore to be of type `Loader`.",
                    fix="Provide `dumper` of type Sequence[Dumper] or `DumperFactory` or `loader` of type `Loader`."
                )
        else:
            if isinstance(self.loader, Loader):
                dumper_type_name = type(self.dumper).__name__

                if isinstance(self.dumper, DumperFactory):
                    dumper_type_name = f"`{dumper_type_name}`"

                raise AssetDefinitionError(
                    error=f"`loader` is of type `Loader` but `dumper` is of type {dumper_type_name}.",
                    explanation=f"`loader` of type `Loader` implies loading a single element, "
                                "which forces `dumper` to dump only one element, and therefore to be of type `Dumper`.",
                    fix="Provide `loader` of type Sequence[Loader] or `LoaderFactory` or `dumper` of type `Dumper`."
                )
            else:
                self.__configure_composite_intermediate_asset()

    def __configure_atomic_intermediate_asset(self):
        # dumper = Dumper => no children => no need of combiner as every dependency must be gathered
        if self.combiner is not None:
            raise AssetDefinitionError(
                error="`combiner` provided with `dumper` of type `Dumper`.",
                explanation="`dumper` of type `Dumper` forces each dependency to be gathered, "
                            "`combiner` is not allowed.",
                fix="Remove `combiner` argument or provide a different `dumper` type "
                    "(`DumperFactory`, Sequence[Dumper]).",
            )

        # Warning if executor provided
        if self.executor is not None:
            raise AssetDefinitionError(
                error="`executor` provided with `dumper` of type `Dumper`.",
                explanation="`dumper` of type `Dumper` forces logic to be computed once by gathering the dependencies. "
                            "Executor is useless.",
                fix="Remove `executor` argument or provide a different `dumper` type "
                    "(`DumperFactory`, Sequence[Dumper])."
            )
        # Warning if no dependencies
        if not self.dependencies:
            warnings.warn(
                "No `dependencies` provided while the asset has a computation logic. "
                "Please verify that the `logic` is not acting as a loader, and that any external inputs "
                "that could be modeled as assets are properly defined as assets with loaders.",
                UserWarning,
                stacklevel=2,
            )

        # Nothing else to do, the asset is well-defined

    def __configure_composite_intermediate_asset(self):
        if isinstance(self.dumper, DumperFactory):
            if not self.dependencies:
                raise AssetDefinitionError(
                    error="`dumper` is of type `DumperFactory` but no `dependencies` provided.",
                    explanation=(
                        "Dumper factories are reserved for dynamically generating dumpers based on "
                        "combinations of dependency results."
                    ),
                    fix=(
                        "Provide `dependencies` argument "
                        "or provide a `dumper` of type `Dumper` and a `loader` of type `Loader`."
                    ),
                )
            if self.combiner is None:
                raise AssetDefinitionError(
                    error="`dumper` is of type `DumperFactory` but no `combiner` provided.",
                    explanation="The default combiner gathers the dependencies, prohibiting multiple dumpers.",
                    fix="Provide `combiner` argument "
                        "or provide a `dumper` of type `Dumper` and a `loader` of type `Loader`."
                )

            if isinstance(self.loader, LoaderFactory):
                logic_inputs_combinations = self.combiner.combine(**self.dependencies)
                for logic_inputs in logic_inputs_combinations:
                    self.children.append(
                        self.__class__(
                            logic=self.logic,
                            dumper=self.dumper.build(**logic_inputs),
                            loader=self.loader.build(**logic_inputs),
                            dependencies=logic_inputs,
                            **self.__extra
                        )
                    )
            else:
                logic_inputs_combinations = list(self.combiner.combine(**self.dependencies))
                n_combinations = len(logic_inputs_combinations)
                n_loaders = len(self.loader)
                if n_combinations != n_loaders:
                    raise AssetDefinitionError(
                        error=f"Mismatching number of loaders.",
                        explanation=f"`combiner` generates {n_combinations} inputs on which to apply the logic, "
                                    f"but `loader` provides {n_loaders} loaders to load the results.",
                        fix=f"Provide `loader` of type Sequence[Loader] with matching number of loaders ({n_combinations}), "
                            "or provide `loader` of type `LoaderFactory` to dynamically generate the loaders."
                    )
                for i, logic_inputs in enumerate(logic_inputs_combinations):
                    self.children.append(
                        self.__class__(
                            logic=self.logic,
                            dumper=self.dumper.build(**logic_inputs),
                            loader=self.loader[i],
                            dependencies=logic_inputs,
                            **self.__extra
                        )
                    )
        else:
            if not self.dependencies:
                raise AssetDefinitionError(
                    error="`dumper` is of type Sequence[Dumper] but no `dependencies` provided.",
                    explanation="Without dependencies, the logic returns the same result, prohibiting multiple dumpers.",
                    fix="Provide `dependencies` argument or provide a `dumper` of type `Dumper`."
                )

            if self.combiner is None:
                raise AssetDefinitionError(
                    error="`dumper` is of type Sequence[Dumper] but no `combiner` provided.",
                    explanation="The default combiner gathers the dependencies, prohibiting multiple dumpers.",
                    fix="Provide `combiner` argument or provide a `dumper` of type `Dumper`."
                )
            if isinstance(self.loader, LoaderFactory):
                logic_inputs_combinations = list(self.combiner.combine(**self.dependencies))
                n_combinations = len(logic_inputs_combinations)
                n_dumpers = len(self.dumper)
                if n_combinations != n_dumpers:
                    raise AssetDefinitionError(
                        error=f"Mismatching number of dumpers.",
                        explanation=f"`combiner` generates {n_combinations} inputs on which to apply the logic, "
                                    f"but `dumper` provides {n_dumpers} dumpers to persist the results.",
                        fix=f"Provide `dumper` of type Sequence[Dumper] with matching number of dumpers ({n_combinations}), "
                            "or provide `dumper` of type `DumperFactory` to dynamically generate the dumpers."
                    )
                for i, logic_inputs in enumerate(logic_inputs_combinations):
                    self.children.append(
                        self.__class__(
                            logic=self.logic,
                            dumper=self.dumper[i],
                            loader=self.loader.build(**logic_inputs),
                            dependencies=logic_inputs,
                            **self.__extra
                        )
                    )
            else:
                logic_inputs_combinations = list(self.combiner.combine(**self.dependencies))
                n_combinations = len(logic_inputs_combinations)
                n_loaders = len(self.loader)
                n_dumpers = len(self.dumper)
                if n_combinations != n_dumpers:
                    raise AssetDefinitionError(
                        error=f"Mismatching number of dumpers.",
                        explanation=f"`combiner` generates {n_combinations} inputs on which to apply the logic, "
                                    f"but `dumper` provides {n_dumpers} dumpers to persist the results.",
                        fix=f"Provide `dumper` of type Sequence[Dumper] with matching number of dumpers ({n_combinations}), "
                            "or provide `dumper` of type `DumperFactory` to dynamically generate the dumpers."
                    )
                if n_combinations != n_loaders:
                    raise AssetDefinitionError(
                        error=f"Mismatching number of loaders.",
                        explanation=f"`combiner` generates {n_combinations} inputs on which to apply the logic, "
                                    f"but `loader` provides {n_loaders} loaders to load the results.",
                        fix=f"Provide `loader` of type Sequence[Loader] with matching number of loaders ({n_combinations}), "
                            "or provide `loader` of type `LoaderFactory` to dynamically generate the loaders."
                    )
                for i, logic_inputs in enumerate(logic_inputs_combinations):
                    self.children.append(
                        self.__class__(
                            logic=self.logic,
                            dumper=self.dumper[i],
                            loader=self.loader[i],
                            dependencies=logic_inputs,
                            **self.__extra
                        )
                    )

    def evaluate(self, **params):
        if self.children:
            return [child.evaluate(**params) for child in self.children]

        if self.logic is None:
            raise RuntimeError(
                "Asset has no logic, `evaluate` method cannot be executed."
            )

        deps_values: Dict[str, Any] = {}
        if self.dependencies:
            for name, dep_asset in self.dependencies.items():
                deps_values[name] = dep_asset.load()

        return self.logic(**deps_values, **params)

    def compute(self, **params):

        sentinel = object()
        provided_executor = params.pop("executor", sentinel)

        if provided_executor is sentinel:
            current_executor = self.executor
        elif isinstance(provided_executor, Executor):
            current_executor = provided_executor
        elif provided_executor is None:
            current_executor = None
        else:
            params["executor"] = provided_executor
            current_executor = self.executor

        if self.children:
            if current_executor is None:
                current_executor = SequentialExecutor()

            def make_task(child):
                return lambda: child.compute(**params)

            tasks: list[Callable[[], None]] = [make_task(child) for child in self.children]
            current_executor.execute(tasks)
        else:
            if self.logic is None:
                raise RuntimeError(
                    "Asset has no logic, `compute` method cannot be executed."
                )

            result = self.evaluate(**params)
            self.dumper.dump(result)

    def load(self) -> Any:
        if self.children:
            return [child.load() for child in self.children]

        if self.loader is None:
            raise RuntimeError(
                "Asset has no loader, `load` method cannot be executed."
            )

        if isinstance(self.loader, Loader):
            return self.loader.load()

        raise RuntimeError(
            "`load` called on atomic asset with non-atomic loader configuration."
        )

    @staticmethod
    def from_logic(
            *,
            dumper: Optional[Union[Dumper, Sequence[Dumper], DumperFactory]] = None,
            loader: Optional[Union[Loader, Sequence[Loader], LoaderFactory]] = None,
            combiner: Optional[Combiner] = None,
            executor: Optional[Executor] = None,
            dependencies: Optional[Mapping[str, "Asset"]] = None,
            **extra: Any,
    ) -> Callable[[Callable[..., Any]], "Asset"]:

        def decorator(func: Callable[..., Any]) -> "Asset":
            inferred_deps: Dict[str, Asset] = {}

            sig = inspect.signature(func)
            for name, param in sig.parameters.items():
                annotation = param.annotation

                if annotation is inspect.Parameter.empty:
                    continue

                origin = get_origin(annotation)
                if origin is Dependency:
                    args = get_args(annotation)
                    if len(args) != 2:
                        raise TypeError(
                            f"Parameter `{name}` annotated with Dependency must have "
                            f"exactly two arguments: Dependency[value_type, asset]. "
                            f"Got: {annotation!r}"
                        )

                    value_type, asset_ref = args

                    if not isinstance(asset_ref, Asset):
                        raise TypeError(
                            f"Second argument of Dependency for parameter `{name}` "
                            f"must be an Asset instance, got {type(asset_ref)!r}."
                        )

                    inferred_deps[name] = asset_ref

            if dependencies is not None:
                final_deps: Dict[str, Asset] = dict(inferred_deps)
                final_deps.update(dependencies)
            else:
                final_deps = inferred_deps if inferred_deps else None

            logic = FunctionLogic(func)

            asset = Asset(
                logic=logic,
                dumper=dumper,
                loader=loader,
                dependencies=final_deps,
                combiner=combiner,
                executor=executor,
                **extra,
            )
            return asset

        return decorator
