#include "FiniteField.h"

#include <algorithm>

const SymbolType* FiniteField::mulTable = mulTable_O8;
const SymbolType* FiniteField::divTable = divTable_O8;

SymbolType ** newMat(int row, int col) {
    SymbolType ** p = new SymbolType*[row];
    for(int i = 0 ; i < row; i ++){
        p[i] = new SymbolType[col];
        memset(p[i], 0, col * sizeof(SymbolType));
    }
    return p;
}

void delMat(SymbolType ** p, int row) {
    for(int i = 0 ; i < row; i ++)
        delete[] p[i];
    delete[] p;
}

SymbolType ** newIdentityMat(int n) {
    SymbolType ** p = newMat(n, n);
    for (int i = 0; i < n; i ++)
        p[i][i] = 1;
    return p;
}

// z[] = y * x[]
void FiniteField::mulVec(SymbolType* z, const SymbolType* x, SymbolType y, int size) {
	int i,  y_index;

    if (y == 0) {
        memset(z, 0, size * sizeof(SymbolType));
        return;
    }

    y_index = y << FIELD_ORDER;

    while (size >= 16) {
        z[0] = mulTable[y_index | x[0]];
        z[1] = mulTable[y_index | x[1]];
        z[2] = mulTable[y_index | x[2]];
        z[3] = mulTable[y_index | x[3]];
        z[4] = mulTable[y_index | x[4]];
        z[5] = mulTable[y_index | x[5]];
        z[6] = mulTable[y_index | x[6]];
        z[7] = mulTable[y_index | x[7]];
        z[8] = mulTable[y_index | x[8]];
        z[9] = mulTable[y_index | x[9]];
        z[10] = mulTable[y_index | x[10]];
        z[11] = mulTable[y_index | x[11]];
        z[12] = mulTable[y_index | x[12]];
        z[13] = mulTable[y_index | x[13]];
        z[14] = mulTable[y_index | x[14]];
        z[15] = mulTable[y_index | x[15]];

        x += 16;
        z += 16;
        size -= 16;
    }

    for (i = 0; i < size; i++) {
        z[i] = mulTable[y_index | x[i]];
    }

}

// x[] = y * x[]
void FiniteField::mulVec(SymbolType* x, SymbolType y, int size) {
	int i, y_index;
    if (y == 0) {
        //d_log("ff_mulv_local: zero\n");
        memset(x, 0, size * sizeof(SymbolType));
        return;
    }

    y_index = y << FIELD_ORDER;

    while (size >= 16) {
        x[0] = mulTable[y_index | x[0]];
        x[1] = mulTable[y_index | x[1]];
        x[2] = mulTable[y_index | x[2]];
        x[3] = mulTable[y_index | x[3]];
        x[4] = mulTable[y_index | x[4]];
        x[5] = mulTable[y_index | x[5]];
        x[6] = mulTable[y_index | x[6]];
        x[7] = mulTable[y_index | x[7]];
        x[8] = mulTable[y_index | x[8]];
        x[9] = mulTable[y_index | x[9]];
        x[10] = mulTable[y_index | x[10]];
        x[11] = mulTable[y_index | x[11]];
        x[12] = mulTable[y_index | x[12]];
        x[13] = mulTable[y_index | x[13]];
        x[14] = mulTable[y_index | x[14]];
        x[15] = mulTable[y_index | x[15]];

        x += 16;
        size -= 16;

    }
    for (i = 0; i < size; i++) {
        x[i] = mulTable[y_index | x[i]];
    }
}

// z[] += y * x[]
void FiniteField::addMulVec(SymbolType* z, const SymbolType* x, SymbolType y, int size) {
    int i;
	int y_index;

	if (y == 0) {

		return;
	}

	y_index = y << FIELD_ORDER;

    while (size >= 16) {
		z[0] ^= mulTable[y_index | x[0]];
		z[1] ^= mulTable[y_index | x[1]];
		z[2] ^= mulTable[y_index | x[2]];
		z[3] ^= mulTable[y_index | x[3]];
		z[4] ^= mulTable[y_index | x[4]];
		z[5] ^= mulTable[y_index | x[5]];
		z[6] ^= mulTable[y_index | x[6]];
		z[7] ^= mulTable[y_index | x[7]];
		z[8] ^= mulTable[y_index | x[8]];
		z[9] ^= mulTable[y_index | x[9]];
		z[10] ^= mulTable[y_index | x[10]];
		z[11] ^= mulTable[y_index | x[11]];
		z[12] ^= mulTable[y_index | x[12]];
		z[13] ^= mulTable[y_index | x[13]];
		z[14] ^= mulTable[y_index | x[14]];
		z[15] ^= mulTable[y_index | x[15]];

		z += 16;
		x += 16;
		size -= 16;

	}

    for (i = 0; i < size; i++) {
		z[i] ^= mulTable[y_index | x[i]];
	}

}

void FiniteField::mulMat(SymbolType* z, SymbolType** x, SymbolType* y, int col, int row) {
    mulVec(z, x[0], y[0], row);
    for (int i = 1; i < col; i ++)
        addMulVec(z, x[i], y[i], row);
}

int FiniteField::getRank(SymbolType** mat, int col, int row) {
    int maxRank = std::min(row, col);
    for (int i = 0, r = 0; i < maxRank; i ++) {
        int nonZeroCol = -1;
        while (true) {
            for (int j = i; j < col; j ++) {
                if (mat[j][r] != 0) {
                    nonZeroCol = j;
                    break;
                }
            }
            if (nonZeroCol < 0) {
                r ++;
                if (r >= row)
                    return i;

                continue;
            }
            std::swap(mat[i], mat[nonZeroCol]);
            break;
        }

        for (int j = row - 1; j >= r; j --)
            mat[i][j] = divElem(mat[i][j], mat[i][r]);

        for (int k = i + 1; k < col; k ++) {
            if (mat[k][r] != 0) {
                for (int j = row - 1; j >= r; j --)
                    mat[k][j] = subElem(mat[k][j], mulElem(mat[i][j], mat[k][r]));
            }
        }
    }

    return maxRank;
}

// assume mat use row reduce, size of invMat is col
//		[_, _, _, _]	[_, ...(packet_size)]		[_, ...(packet_size)]
//		[_, _, _, _]	[_, ...]					[_, ...]
//		[_, _, _, _] * 	[_, ...]			   =	[_, ...]
//		[_, _, _, _]	[_, ...]					[_, ...]
//		[_, _, _, _]								[_, ...]
//			(GH)		(raw 4 packets)				(gen 5 new packets)
//
// NOTE: column reduce, column reduce, column reduce
int FiniteField::gaussianElimination(SymbolType** mat, SymbolType** invMat, int col, int row) {

    for (int i = 0; i < row; i ++) {
        int nonZeroCol = -1;
        for (int j = i; j < col; j ++) {
            if (mat[j][i] != 0) {
                nonZeroCol = j;
                break;
            }
        }

        if (nonZeroCol < 0)
            return i;

        std::swap(mat[nonZeroCol], mat[i]);
        std::swap(invMat[nonZeroCol], invMat[i]);

        {
            SymbolType c = divElem(1, mat[i][i]);
            for (int j = row - 1; j >= i; j --)
                mat[i][j] = mulElem(mat[i][j], c);
            mulVec(invMat[i], c, col);
        }

        for (int k = 0; k < col; k ++) {
            if (k == i || !mat[k][i]) continue;
            SymbolType c = mat[k][i];
            for (int j = row - 1; j >= i; j --) {
                mat[k][j] = subElem(mat[k][j], mulElem(mat[i][j], c));
            }
            addMulVec(invMat[k], invMat[i], c, col);
        }
    }

    return row;
}

//  x * A = y
//  x * A * P = y * P
//  x * [I 0] = y * P
//
//  P called invA

int FiniteField::gaussianSolve(SymbolType** A, SymbolType** Y, SymbolType** X, int rowA, int col, int rowY) {
    SymbolType** invA = newIdentityMat(col);

    int rank = gaussianElimination(A, invA, col, rowA);

    if (rank == rowA) {
        for (int i = 0; i < rank; i ++) {
            mulMat(X[i], Y, invA[i], col, rowY);
        }
    }

    delMat(invA, col);

    return rank;
}
