// SPDX-License-Identifier: MIT
pragma solidity ^0.8.12;

import "@openzeppelin-upgradeable/contracts/token/ERC721/ERC721Upgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721EnumerableUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721RoyaltyUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/access/AccessControlEnumerableUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/proxy/utils/Initializable.sol";

import "../../interfaces/IHighriseLand.sol";
import "../opensea/Utils.sol";

contract HighriseLandAlt is
    Initializable,
    ERC721Upgradeable,
    ERC721EnumerableUpgradeable,
    ERC721RoyaltyUpgradeable,
    AccessControlEnumerableUpgradeable,
    IHighriseLand
{
    // CONSTANTS
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant ESTATE_MANAGER_ROLE = keccak256("ESTATE_MANAGER");
    bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");
    // STORAGE
    string private _baseTokenURI;
    ProxyRegistry private _openseaProxyRegistry;
    // ALT STORAGE
    uint256 private _val;

    /// Do not leave an implementation contract uninitialized. An uninitialized implementation contract can be taken over by an attacker, which may impact the proxy
    /// Including a constructor to automatically mark it as initialized.
    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() initializer {}

    // ------------------------------ INITIALIZER ---------------------------------------------------------------------------
    function initialize(
        string memory name,
        string memory symbol,
        string memory baseTokenURI,
        address openseaProxyRegistry
    ) public virtual initializer {
        __HighriseLandAlt_init(
            name,
            symbol,
            baseTokenURI,
            openseaProxyRegistry
        );
    }

    function __HighriseLandAlt_init(
        string memory name,
        string memory symbol,
        string memory baseTokenURI,
        address openseaProxyRegistry
    ) internal onlyInitializing {
        __ERC721_init(name, symbol);
        __ERC721Enumerable_init();
        __ERC721Royalty_init();
        __AccessControlEnumerable_init();
        __HighriseLandAlt_init_unchained(
            name,
            symbol,
            baseTokenURI,
            openseaProxyRegistry
        );
    }

    function __HighriseLandAlt_init_unchained(
        string memory,
        string memory,
        string memory baseTokenURI,
        address openseaProxyRegistry
    ) internal onlyInitializing {
        _baseTokenURI = baseTokenURI;
        _openseaProxyRegistry = ProxyRegistry(openseaProxyRegistry);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(ESTATE_MANAGER_ROLE, msg.sender);
        _grantRole(OWNER_ROLE, msg.sender);
        _setDefaultRoyalty(msg.sender, 500);
    }

    // ----------------------------------------------------------------------------------------------------------------------

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
            AccessControlEnumerableUpgradeable,
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

    /**
     * Override grantRole so that only one owner is allowd
     */
    function grantRole(bytes32 role, address account)
        public
        virtual
        override(IAccessControlUpgradeable, AccessControlUpgradeable)
        onlyRole(getRoleAdmin(role))
    {
        require(
            role != OWNER_ROLE || getRoleMemberCount(OWNER_ROLE) == 0,
            "There can be only one owner"
        );
        _grantRole(role, account);
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

    function setBaseTokenURI(string memory baseTokenURI)
        public
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        _baseTokenURI = baseTokenURI;
    }

    // ---------------------------------------------------------------------------------

    // ------------------------- OWNERSHIP ---------------------------------------------
    /**
     * @dev Returns the address of the current owner.
     * Only one wallet can have owner role at the time.
     * Ensured by grantRole override.
     */
    function owner() public view returns (address) {
        return getRoleMember(OWNER_ROLE, 0);
    }

    // ---------------------------------------------------------------------------------

    // ----------------------- OPEN SEA REGISTRY ---------------------------------------
    /**
     * Override isApprovedForAll to whitelist user's OpenSea proxy accounts to enable gas-less listings.
     */
    function isApprovedForAll(address owner, address operator)
        public
        view
        override(ERC721Upgradeable, IERC721Upgradeable)
        returns (bool)
    {
        // Whitelist OpenSea proxy contract for easy trading.
        return
            address(_openseaProxyRegistry.proxies(owner)) == operator ||
            super.isApprovedForAll(owner, operator);
    }

    // ---------------------------------------------------------------------------------

    // ---------------- ALT FUNCTIONS -------------------------------------------------
    function storeValue(uint256 val) public onlyRole(DEFAULT_ADMIN_ROLE) {
        _val = val;
    }

    function getValue() public view returns (uint256) {
        return _val;
    }
}
