#ifndef FINITEFIELD_H_
#define FINITEFIELD_H_

#include <cstring>

#include "MulTable_O8.h"
#include "DivTable_O8.h"

SymbolType ** newMat(int row, int col);
void delMat(SymbolType ** p, int row);

class FiniteField {
public:
    // binary field: return z[pos]
    static SymbolType getBinElem(const SymbolType* z, int pos);

    // binary field: z[pos] = val
    static void setBinElem(SymbolType* z, int pos, bool val);

	static inline SymbolType addElem(SymbolType x, SymbolType y) {
		return x ^ y;
	}

    static inline SymbolType addElemLocal(SymbolType& x, SymbolType y) {
        return x ^= y;
    }

	static inline SymbolType subElem(SymbolType x, SymbolType y) {
		return x ^ y;
	}

	static inline SymbolType mulElem(SymbolType x, SymbolType y) {
		return mulTable[(x << FIELD_ORDER) | y];
	}

	static inline SymbolType divElem(SymbolType x, SymbolType y) {
		return divTable[(x << FIELD_ORDER) | y];
	}

	// z[] = y * x[]
	static void mulVec(SymbolType* z, const SymbolType* x, SymbolType y, int size);

	// x[] = y * x[]
	static void mulVec(SymbolType* x, SymbolType y, int size);

	// z[] = z[] + y * x[]
	static void addMulVec(SymbolType* z, const SymbolType* x, SymbolType y, int size);

	// z[] = x[][] * y[]
	static void mulMat(SymbolType* z, SymbolType** x, SymbolType* y, int col, int row);

	// return rank
	static int getRank(SymbolType**, int col, int row);

	// set inverse matrix [A, I] --> [I, A^-1], return rank
	static int gaussianElimination(SymbolType** A, SymbolType** invA, int col, int row);

	// solve A * x = Y --> x = A^-1 * Y
	static int gaussianSolve(SymbolType** A, SymbolType** Y, SymbolType** X, int rowA, int col, int rowY);

private:
    static const SymbolType* mulTable;
    static const SymbolType* divTable;
};


#endif /* FINITEFIELD_H_ */
