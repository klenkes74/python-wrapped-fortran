# Makefile für die FORTRAN-Bibliothek und Programme

# Compiler und Optionen
FC = gfortran
FFLAGS = -O2 -Wall

# Verzeichnisse
SRC_DIR = src
BIN_DIR = bin
OBJ_DIR = obj

# Erstelle Verzeichnisse, falls sie nicht existieren
$(shell mkdir -p $(BIN_DIR) $(OBJ_DIR))

# Quelldateien und Objektdateien
LIB_SRC = $(SRC_DIR)/math_operations.f90
LIB_OBJ = $(OBJ_DIR)/math_operations.o

# Einzelne Programme und das neue Calculator-Programm
PROGS = calculator
PROG_OBJS = $(patsubst %,$(OBJ_DIR)/%.o,$(PROGS))
PROG_BINS = $(patsubst %,$(BIN_DIR)/%,$(PROGS))

# Hauptziel: Alle Programme erstellen
all: $(LIB_OBJ) $(PROG_BINS)

# Regel für die Bibliothek
$(LIB_OBJ): $(LIB_SRC)
	$(FC) $(FFLAGS) -c $< -o $@

# Regel für die Programme
$(BIN_DIR)/%: $(OBJ_DIR)/%.o $(LIB_OBJ)
	$(FC) $(FFLAGS) $^ -o $@

# Regel für Programmobjektdateien
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.f90
	$(FC) $(FFLAGS) -c $< -o $@

# Aufräumen
clean:
	rm -f $(OBJ_DIR)/*.o $(BIN_DIR)/*

# Module-Info aufräumen
cleanmod:
	rm -f *.mod

# Alles aufräumen
cleanall: clean cleanmod
	rm -rf $(BIN_DIR) $(OBJ_DIR)

# Phony-Ziele
.PHONY: all clean cleanmod cleanall