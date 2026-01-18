/*
 * schemaUtils.ts
 * Copyright (c) Microsoft Corporation.
 * Licensed under the MIT license.
 *
 * Helper functions for querying schema-defined types (dataclasses,
 * TypedDicts, NamedTuples).
 */

import { ClassType, ClassTypeFlags, combineTypes, isClass, isClassInstance, isTypeVar, isUnion, Type } from './types';
import { TypeEvaluator } from './typeEvaluatorTypes';
import { getTypedDictMembersForClass } from './typedDicts';
import { applySolvedTypeVars, buildSolutionFromSpecializedClass } from './typeUtils';

export function isSchemaClassType(t: ClassType): boolean {
    if (ClassType.isDataClass(t)) {
        return true;
    }

    if (ClassType.isTypedDictClass(t)) {
        return true;
    }

    if (t.shared.mro.some((m) => isClass(m) && m.shared.namedTupleEntries)) {
        return true;
    }

    return false;
}

export function getSchemaFieldNames(evaluator: TypeEvaluator, t: Type): string[] | undefined {
    if (isClass(t)) {
        if (ClassType.isDataClass(t)) {
            const entries: string[] = [];
            const nameMap = new Set<string>();
            const symbolTable = ClassType.getSymbolTable(t);

            for (const mroClass of t.shared.mro) {
                if (isClass(mroClass)) {
                    const localEntries = ClassType.getDataClassEntries(mroClass);
                    for (const entry of localEntries) {
                        if (!nameMap.has(entry.name)) {
                            nameMap.add(entry.name);
                            if (entry.isClassVar) {
                                continue;
                            }
                            if (isClass(entry.type) && ClassType.isBuiltIn(entry.type, 'KW_ONLY')) {
                                continue;
                            }
                            const symbol = symbolTable.get(entry.name);
                            if (symbol?.isInitVar()) {
                                continue;
                            }
                            entries.push(entry.name);
                        }
                    }
                }
            }
            return entries;
        }

        if (ClassType.isTypedDictClass(t)) {
            const entries = getTypedDictMembersForClass(evaluator, t);
            return Array.from(entries.knownItems.keys());
        }

        let isNamedTuple = false;
        const entries: string[] = [];
        const nameMap = new Set<string>();
        for (const mroClass of t.shared.mro) {
            if (isClass(mroClass) && mroClass.shared.namedTupleEntries) {
                isNamedTuple = true;
                for (const name of mroClass.shared.namedTupleEntries) {
                    if (!nameMap.has(name)) {
                        entries.push(name);
                        nameMap.add(name);
                    }
                }
            }
        }
        if (isNamedTuple) {
            return entries;
        }
    } else if (isUnion(t)) {
        let intersection: string[] | undefined;
        for (const subtype of t.priv.subtypes) {
            const names = getSchemaFieldNames(evaluator, subtype);
            if (names === undefined) {
                return undefined;
            }
            if (intersection === undefined) {
                intersection = names;
            } else {
                intersection = intersection.filter((name) => names!.includes(name));
            }
        }
        return intersection;
    } else if (isTypeVar(t)) {
        if (t.shared.boundType) {
            return getSchemaFieldNames(evaluator, t.shared.boundType);
        }
    }

    return undefined;
}

// Version of getSchemaFieldNames that doesn't require TypeEvaluator.
// This is used during type variable substitution where we don't have
// access to the evaluator. It works for dataclasses and NamedTuples
// but returns undefined for TypedDicts (they will be handled later).
export function getSchemaFieldNamesWithoutEvaluator(t: Type): string[] | undefined {
    if (isClass(t)) {
        if (ClassType.isDataClass(t)) {
            const entries: string[] = [];
            const nameMap = new Set<string>();
            const symbolTable = ClassType.getSymbolTable(t);

            for (const mroClass of t.shared.mro) {
                if (isClass(mroClass)) {
                    const localEntries = ClassType.getDataClassEntries(mroClass);
                    for (const entry of localEntries) {
                        if (!nameMap.has(entry.name)) {
                            nameMap.add(entry.name);
                            if (entry.isClassVar) {
                                continue;
                            }
                            if (isClass(entry.type) && ClassType.isBuiltIn(entry.type, 'KW_ONLY')) {
                                continue;
                            }
                            const symbol = symbolTable.get(entry.name);
                            if (symbol?.isInitVar()) {
                                continue;
                            }
                            entries.push(entry.name);
                        }
                    }
                }
            }
            return entries;
        }

        // For TypedDict, we cannot resolve without TypeEvaluator.
        // Return undefined and let the caller handle it.
        if (ClassType.isTypedDictClass(t)) {
            // Try to get entries from the typedDictEntries if available
            const entries = t.shared.typedDictEntries;
            if (entries) {
                return Array.from(entries.knownItems.keys());
            }
            return undefined;
        }

        let isNamedTuple = false;
        const entries: string[] = [];
        const nameMap = new Set<string>();
        for (const mroClass of t.shared.mro) {
            if (isClass(mroClass) && mroClass.shared.namedTupleEntries) {
                isNamedTuple = true;
                for (const name of mroClass.shared.namedTupleEntries) {
                    if (!nameMap.has(name)) {
                        entries.push(name);
                        nameMap.add(name);
                    }
                }
            }
        }
        if (isNamedTuple) {
            return entries;
        }
    } else if (isUnion(t)) {
        let intersection: string[] | undefined;
        for (const subtype of t.priv.subtypes) {
            const names = getSchemaFieldNamesWithoutEvaluator(subtype);
            if (names === undefined) {
                return undefined;
            }
            if (intersection === undefined) {
                intersection = names;
            } else {
                intersection = intersection.filter((name) => names!.includes(name));
            }
        }
        return intersection;
    } else if (isTypeVar(t)) {
        if (t.shared.boundType) {
            return getSchemaFieldNamesWithoutEvaluator(t.shared.boundType);
        }
    }

    return undefined;
}

// Gets the field type for a given key on a schema type.
// The keyType can be a single Literal string or a union of Literal strings.
// Returns the union of field types for all keys, or undefined if any key is invalid.
export function getSchemaFieldTypeForKey(targetType: Type, keyType: Type): Type | undefined {
    if (isTypeVar(keyType)) {
        const fieldNames = getSchemaFieldNamesWithoutEvaluator(targetType);
        if (!fieldNames || fieldNames.length === 0) {
            return undefined;
        }

        const fieldTypes: Type[] = [];
        for (const fieldName of fieldNames) {
            const fieldType = getSchemaFieldTypeWithoutEvaluator(targetType, fieldName);
            if (fieldType) {
                fieldTypes.push(fieldType);
            }
        }

        return combineTypes(fieldTypes);
    }

    // Extract literal string values from keyType
    const keyNames: string[] = [];

    if (isClassInstance(keyType) && ClassType.isBuiltIn(keyType, 'str')) {
        const literalValue = keyType.priv.literalValue;
        if (typeof literalValue === 'string') {
            keyNames.push(literalValue);
        } else {
            // Non-literal string - cannot resolve
            return undefined;
        }
    } else if (isUnion(keyType)) {
        for (const subtype of keyType.priv.subtypes) {
            if (isClassInstance(subtype) && ClassType.isBuiltIn(subtype, 'str')) {
                const literalValue = subtype.priv.literalValue;
                if (typeof literalValue === 'string') {
                    keyNames.push(literalValue);
                } else {
                    return undefined;
                }
            } else {
                return undefined;
            }
        }
    } else {
        return undefined;
    }

    if (keyNames.length === 0) {
        return undefined;
    }

    // Get field types for each key
    const fieldTypes: Type[] = [];
    for (const keyName of keyNames) {
        const fieldType = getSchemaFieldTypeWithoutEvaluator(targetType, keyName);
        if (fieldType === undefined) {
            return undefined;
        }
        fieldTypes.push(fieldType);
    }

    return combineTypes(fieldTypes);
}

// Version of getSchemaFieldType that doesn't require TypeEvaluator.
function getSchemaFieldTypeWithoutEvaluator(t: Type, fieldName: string): Type | undefined {
    if (isClass(t)) {
        if (ClassType.isDataClass(t)) {
            const symbolTable = ClassType.getSymbolTable(t);
            for (const mroClass of t.shared.mro) {
                if (isClass(mroClass)) {
                    const entries = ClassType.getDataClassEntries(mroClass);
                    const entry = entries.find((e) => e.name === fieldName);
                    if (entry) {
                        if (entry.isClassVar) {
                            return undefined;
                        }
                        const symbol = symbolTable.get(fieldName);
                        if (symbol?.isInitVar()) {
                            return undefined;
                        }

                        const solution = buildSolutionFromSpecializedClass(t);
                        return applySolvedTypeVars(entry.type, solution);
                    }
                }
            }
        }

        if (ClassType.isTypedDictClass(t)) {
            // Try to get from typedDictEntries if available
            const entries = t.shared.typedDictEntries;
            if (entries) {
                const entry = entries.knownItems.get(fieldName);
                if (entry) {
                    return entry.valueType;
                }
            }
            return undefined;
        }

        for (const mroClass of t.shared.mro) {
            if (isClass(mroClass) && mroClass.shared.namedTupleEntries?.has(fieldName)) {
                // For NamedTuple, we need the evaluator to get the field type.
                // Return undefined and let the caller handle it.
                return undefined;
            }
        }
    } else if (isUnion(t)) {
        const types: Type[] = [];
        for (const subtype of t.priv.subtypes) {
            const fieldType = getSchemaFieldTypeWithoutEvaluator(subtype, fieldName);
            if (!fieldType) {
                return undefined;
            }
            types.push(fieldType);
        }
        return combineTypes(types);
    } else if (isTypeVar(t)) {
        if (t.shared.boundType) {
            return getSchemaFieldTypeWithoutEvaluator(t.shared.boundType, fieldName);
        }
    }

    return undefined;
}

export function getSchemaFieldType(evaluator: TypeEvaluator, t: Type, fieldName: string): Type | undefined {
    if (isClass(t)) {
        if (ClassType.isDataClass(t)) {
            const symbolTable = ClassType.getSymbolTable(t);
            for (const mroClass of t.shared.mro) {
                if (isClass(mroClass)) {
                    const entries = ClassType.getDataClassEntries(mroClass);
                    const entry = entries.find((e) => e.name === fieldName);
                    if (entry) {
                        if (entry.isClassVar) {
                            return undefined;
                        }
                        const symbol = symbolTable.get(fieldName);
                        if (symbol?.isInitVar()) {
                            return undefined;
                        }

                        const solution = buildSolutionFromSpecializedClass(t);
                        return applySolvedTypeVars(entry.type, solution);
                    }
                }
            }
        }

        if (ClassType.isTypedDictClass(t)) {
            const entries = getTypedDictMembersForClass(evaluator, t);
            const entry = entries.knownItems.get(fieldName);
            if (entry) {
                return entry.valueType;
            }
        }

        for (const mroClass of t.shared.mro) {
            if (isClass(mroClass) && mroClass.shared.namedTupleEntries?.has(fieldName)) {
                const symbol = ClassType.getSymbolTable(t).get(fieldName);
                if (symbol) {
                    const solution = buildSolutionFromSpecializedClass(t);
                    return applySolvedTypeVars(evaluator.getEffectiveTypeOfSymbol(symbol), solution);
                }
            }
        }
    } else if (isUnion(t)) {
        const types: Type[] = [];
        for (const subtype of t.priv.subtypes) {
            const fieldType = getSchemaFieldType(evaluator, subtype, fieldName);
            if (!fieldType) {
                return undefined;
            }
            types.push(fieldType);
        }
        return combineTypes(types);
    } else if (isTypeVar(t)) {
        if (t.shared.boundType) {
            return getSchemaFieldType(evaluator, t.shared.boundType, fieldName);
        }
    }

    return undefined;
}
