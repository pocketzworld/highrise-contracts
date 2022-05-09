// SPDX-License-Identifier: MIT
pragma solidity =0.8.12;

import "@openzeppelin-upgradeable/contracts/token/ERC721/ERC721Upgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721EnumerableUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721RoyaltyUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/access/AccessControlEnumerableUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/utils/ERC721HolderUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/utils/introspection/ERC165Checker.sol";

import "../opensea/Utils.sol";

contract HighriseEstate is
    Initializable,
    ERC721Upgradeable,
    ERC721EnumerableUpgradeable,
    ERC721HolderUpgradeable,
    ERC721RoyaltyUpgradeable,
    AccessControlEnumerableUpgradeable
{
    using ERC165Checker for address;

    event EstateMinted(uint256 tokenId, address to, uint32[] parcelIds);

    // CONSTANTS
    bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");

    // ------------------------ STORAGE --------------------------------------
    string private _baseTokenURI;
    address private _land;
    mapping(uint256 => uint256[]) public estatesToParcels;
    ProxyRegistry private _openseaProxyRegistry;

    // -----------------------------------------------------------------------

    // ------------------------ INITIALIZER -----------------------------------
    /// Do not leave an implementation contract uninitialized. An uninitialized implementation contract can be taken over by an attacker, which may impact the proxy
    /// Including a constructor to automatically mark it as initialized.
    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() initializer {}

    function initialize(
        string memory name,
        string memory symbol,
        string memory baseTokenURI,
        address land,
        address openseaProxyRegistry
    ) public virtual initializer {
        require(
            land.supportsInterface(type(IERC721).interfaceId),
            "IS_NOT_ERC721_CONTRACT"
        );
        __HighriseEstate_init(
            name,
            symbol,
            baseTokenURI,
            land,
            openseaProxyRegistry
        );
    }

    function __HighriseEstate_init(
        string memory name,
        string memory symbol,
        string memory baseTokenURI,
        address land,
        address openseaProxyRegistry
    ) internal onlyInitializing {
        __ERC721_init(name, symbol);
        __ERC721Enumerable_init();
        __ERC721Royalty_init();
        __ERC721Holder_init();
        __AccessControlEnumerable_init();
        __HighriseEstate_init_unchained(
            name,
            symbol,
            baseTokenURI,
            land,
            openseaProxyRegistry
        );
    }

    function __HighriseEstate_init_unchained(
        string memory,
        string memory,
        string memory baseTokenURI,
        address land,
        address openseaProxyRegistry
    ) internal onlyInitializing {
        _baseTokenURI = baseTokenURI;
        _land = land;
        _openseaProxyRegistry = ProxyRegistry(openseaProxyRegistry);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(OWNER_ROLE, msg.sender);
        _setDefaultRoyalty(msg.sender, 500);
    }

    // ------------------------------------------------------------------------

    /**
     * @dev Token URIs will be autogenerated based on `baseURI` and their token IDs.
     * See {ERC721-tokenURI}.
     */
    function _baseURI() internal view virtual override returns (string memory) {
        return _baseTokenURI;
    }

    function parseToCoordinates(uint32 tokenId)
        public
        pure
        returns (int16[2] memory)
    {
        int16 x = int16(int32(tokenId >> 16));
        int16 y = int16(int32(tokenId));
        return [x, y];
    }

    /**
    The expected array shape is:
     | ----------   x
     | [0  1  2]
     | [3  4  5]
     | [6  7  8]
     y
     */
    function _isEstateShapeValid(uint32[] memory parcelIds) internal returns (uint256) {
        uint32 size = 0;
        if (parcelIds.length == 9) {
            // We expect a 3x3 matrix.
            size = 3;
        } else if (parcelIds.length == 36) {
            size = 6;
        } else if (parcelIds.length == 81) {
            size = 9;
        } else if (parcelIds.length == 144) {
            size = 12;
        }
        require(size != 0, "HRESTATE: Invalid estate shape");
        // For each row,
        for (uint32 y = 0; y < size; y++) {
            // For each X except the last,
            for (uint32 x = 0; x < size - 1; x++) {
                uint32 curr = parcelIds[y * size + x];
                uint32 right = parcelIds[y * size + x + 1];
                int16[2] memory currCoords = parseToCoordinates(curr);
                int16[2] memory rightCoords = parseToCoordinates(right);

                // Validate neighboring column
                require(
                    currCoords[0] + 1 == rightCoords[0],
                    "HRESTATE: Invalid coordinates. Land parcels are not adjacent horizontally"
                );
                // Validate that the row is the same
                require(
                    currCoords[1] == rightCoords[1],
                    "HRESTATE: Invalid coordinates. Land parcels in row do not have same vertical coordinate"
                );
                // Validate that rows are one above other
                if (x == 0 && y < size - 1) {
                    uint32 upper = parcelIds[(y + 1) * size + x];
                    int16[2] memory upperCoords = parseToCoordinates(upper);
                    require(
                        currCoords[0] == upperCoords[0],
                        "HRESTATE: Invalid coordinates. Land parcel rows do not have same column coordinates"
                    );
                    require(
                        currCoords[1] + 1 == upperCoords[1],
                        "HRESTATE: Invalid coordinates. Land parcels are not adjacent vertically"
                    );
                }
            }
        }
        // Estate tokenId is the same as land parcel tokenId of top-left coordinate
        return parcelIds[(size - 1) * size];
    }

    function _tokensValid(uint32[] memory tokenIds) internal {
        for (uint32 i = 0; i < tokenIds.length; i++) {
            address owner = IERC721(_land).ownerOf(tokenIds[i]);
            require(msg.sender == owner, "HRESTATE: Sender is not token owner");
            address approved = IERC721(_land).getApproved(tokenIds[i]);
            require(address(this) == approved, "HRESTATE: Estate contract not approved");
        }

    }

    function mintFromParcels(uint32[] memory tokenIds)
        public
        returns (uint256)
    {
        _tokensValid(tokenIds);
        uint256 tokenId = _isEstateShapeValid(tokenIds);
        for (uint32 i = 0; i < tokenIds.length; i++) {
            IERC721(_land).safeTransferFrom(
                msg.sender,
                address(this),
                tokenIds[i]
            );
        }
        estatesToParcels[tokenId] = tokenIds;
        _mint(msg.sender, tokenId);
        emit EstateMinted(tokenId, msg.sender, tokenIds);
        return tokenId;
    }

    function burn(uint256 tokenId) public {
        require(
            _exists(tokenId),
            "ERC721: operator query for nonexistent token"
        );
        require(
            _isApprovedOrOwner(msg.sender, tokenId),
            "ERC721Burnable: caller is not owner nor approved"
        );
        uint256[] memory parcels = estatesToParcels[tokenId];
        for (uint256 i = 0; i < parcels.length; i++) {
            IERC721(_land).safeTransferFrom(
                address(this),
                msg.sender,
                parcels[i]
            );
        }
        _burn(tokenId);
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
        return super.supportsInterface(interfaceId);
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

    // ----------------------- ROYALTY -------------------------------------------------
    function setDefaultRoyalty(address receiver, uint96 feeNumerator)
        public
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        _setDefaultRoyalty(receiver, feeNumerator);
    }
    // ---------------------------------------------------------------------------------
}
