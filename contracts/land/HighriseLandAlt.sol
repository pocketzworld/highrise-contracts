// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import "@openzeppelin-upgradeable/contracts/token/ERC721/ERC721Upgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721EnumerableUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721RoyaltyUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/access/AccessControlUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/proxy/utils/Initializable.sol";

import "../../interfaces/IHighriseLand.sol";

contract HighriseLandAlt is
    Initializable,
    ERC721Upgradeable,
    ERC721EnumerableUpgradeable,
    ERC721RoyaltyUpgradeable,
    AccessControlUpgradeable,
    IHighriseLand
{
    // CONSTANTS
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant ESTATE_MANAGER_ROLE = keccak256("ESTATE_MANAGER");
    // STORAGE
    string private _baseTokenURI;
    // ALT STORAGE
    uint256 private _val;

    /// Do not leave an implementation contract uninitialized. An uninitialized implementation contract can be taken over by an attacker, which may impact the proxy
    /// Including a constructor to automatically mark it as initialized.
    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() initializer {}

    /**
     * @dev Token URIs will be autogenerated based on `baseURI` and their token IDs.
     * See {ERC721-tokenURI}.
     */
    function _baseURI() internal view virtual override returns (string memory) {
        return _baseTokenURI;
    }

    /**
     * @dev Creates a new token for `user` with token ID `tokenId`.
     * Emits {IERC721-Transfer} event)
     * The token URI is autogenerated based on the base URI passed at construction.
     *
     * See {ERC721-_mint}.
     *
     * Requirements:
     *
     * - the caller must have the `MINTER_ROLE`.
     */
    function mint(address user, uint256 tokenId)
        external
        onlyRole(MINTER_ROLE)
    {
        _safeMint(user, tokenId);
    }

    // --------------------------------------- OVERRIDES ---------------------------------------------
    // The following functions are overrides required by Solidity.

    function _burn(uint256 tokenId)
        internal
        override(ERC721Upgradeable, ERC721RoyaltyUpgradeable)
    {
        super._burn(tokenId);
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId
    ) internal override(ERC721Upgradeable, ERC721EnumerableUpgradeable) {
        super._beforeTokenTransfer(from, to, tokenId);
    }

    /**
     * @dev See {IERC165-supportsInterface}.
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(
            AccessControlUpgradeable,
            ERC721Upgradeable,
            ERC721EnumerableUpgradeable,
            ERC721RoyaltyUpgradeable
        )
        returns (bool)
    {
        return
            interfaceId == type(IHighriseLand).interfaceId ||
            super.supportsInterface(interfaceId);
    }

    // -----------------------------------------------------------------------------------------------

    // ----------------------- ESTATES -------------------------------------------------
    function bindToEstate(address owner, uint32[] memory tokenIds)
        external
        onlyRole(ESTATE_MANAGER_ROLE)
    {
        for (uint256 i = 0; i < tokenIds.length; i++) {
            _safeTransfer(owner, msg.sender, tokenIds[i], bytes(""));
        }
    }

    // ---------------------------------------------------------------------------------

    // ----------------------- HELPER LOGIC --------------------------------------------
    function ownerTokens(address owner) public view returns (uint256[] memory) {
        uint256 balance = balanceOf(owner);
        uint256[] memory tokens = new uint256[](balance);

        for (uint256 i = 0; i < balance; i++) {
            tokens[i] = tokenOfOwnerByIndex(owner, i);
        }

        return tokens;
    }

    function setBaseTokenURI(string memory baseTokenURI) public onlyRole(DEFAULT_ADMIN_ROLE) {
        _baseTokenURI = baseTokenURI;
    }
    // ---------------------------------------------------------------------------------

    // ---------------- ALT FUNCTIONS -------------------------------------------------
    function storeValue(uint256 val) public {
        _val = val;
    }

    function getValue() public view returns (uint256) {
        return _val;
    }
}
