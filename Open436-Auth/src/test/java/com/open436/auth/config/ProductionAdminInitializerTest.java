package com.open436.auth.config;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ProductionAdminInitializerTest {

    private static final String VALID_COST_10 =
            "$2a$10$N5u9SIi1PpAXBzfFCF2Bwe4wrY5uD5d0pPD29uHj3NMd9G9SAdIbe";

    @Test
    void acceptsAParsableCost10Hash() {
        assertTrue(ProductionAdminInitializer.isValidBcryptHash(VALID_COST_10));
    }

    @Test
    void rejectsPlaintextGarbageAndWrongCost() {
        assertFalse(ProductionAdminInitializer.isValidBcryptHash("x".repeat(60)));
        assertFalse(ProductionAdminInitializer.isValidBcryptHash(
                VALID_COST_10.replace("$10$", "$12$")));
        assertFalse(ProductionAdminInitializer.isValidBcryptHash(null));
    }
}
